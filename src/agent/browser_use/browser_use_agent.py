from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional, Any, Dict

from browser_use import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class BrowserUseAgent:
    """Wrapper for browser-use Agent with task queue integration"""

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o", enable_vnc: bool = False):
        self.llm_provider = llm_provider
        self.model_name = model_name  # Use gpt-4o which supports vision
        self.enable_vnc = enable_vnc
        self.vnc_server = None
        self.vnc_info = None
        self.llm = self._create_llm()
        self.current_agent: Optional[Agent] = None
        self.is_running = False
        self.is_paused = False
        self.is_stopped = False

    def _create_llm(self):
        """Create LLM instance based on provider"""
        try:
            if self.llm_provider.lower() == "openai":
                # Use environment variable directly
                return ChatOpenAI(model=self.model_name)

            elif self.llm_provider.lower() == "anthropic":
                # Use environment variable directly
                return ChatAnthropic(
                    model_name="claude-3-sonnet-20240229",
                    timeout=60,
                    stop=None
                )

            elif self.llm_provider.lower() == "gemini":
                # Use environment variable directly
                return ChatGoogleGenerativeAI(model="gemini-pro")

            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

        except Exception as e:
            logger.error(f"Failed to create LLM: {e}")
            # Fallback to OpenAI with vision model if available
            try:
                return ChatOpenAI(model="gpt-4o")
            except:
                raise Exception("No valid LLM configuration found")

    async def _setup_vnc_if_enabled(self):
        """Setup VNC server if enabled"""
        if self.enable_vnc:
            try:
                from src.vnc.vnc_server import vnc_manager
                self.vnc_server = await vnc_manager.get_or_create_server("browser_automation")
                self.vnc_info = await vnc_manager.start_server("browser_automation")

                if self.vnc_info.get("status") == "success":
                    logger.info(f"VNC server started for browser automation: {self.vnc_info}")
                else:
                    logger.warning(f"Failed to start VNC server: {self.vnc_info}")
                    self.enable_vnc = False

            except Exception as e:
                logger.error(f"Error setting up VNC: {e}")
                self.enable_vnc = False

    async def _cleanup_vnc(self):
        """Cleanup VNC server"""
        if self.vnc_server:
            try:
                from src.vnc.vnc_server import vnc_manager
                await vnc_manager.stop_server("browser_automation")
                logger.info("VNC server stopped")
            except Exception as e:
                logger.error(f"Error stopping VNC server: {e}")
            finally:
                self.vnc_server = None
                self.vnc_info = None

    async def _create_vnc_agent(self, task: str):
        """Create browser-use Agent configured for VNC display"""
        from browser_use import Agent
        import platform

        # Get VNC display environment
        if not self.vnc_server:
            raise RuntimeError("VNC server not available")

        vnc_env = self.vnc_server.get_display_env()
        display = vnc_env.get('DISPLAY')
        method = getattr(self.vnc_server, 'method_used', 'unknown')

        logger.info(f"Creating VNC-enabled browser on display {display} using {method}")

        # Set environment variables for browser to use VNC display
        original_env = {}
        for key, value in vnc_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # For Windows with WSL/Docker, we need special handling
            if platform.system().lower() == "windows" and method in ["WSL", "Docker"]:
                logger.info(f"Configuring browser for Windows {method} VNC")

                # Create agent with special configuration for Windows VNC
                agent = Agent(
                    task=task,
                    llm=self.llm
                )

                # Additional configuration might be needed here for WSL/Docker integration
                # This depends on how browser-use handles cross-platform display forwarding

            else:
                # Standard Linux/macOS VNC configuration
                agent = Agent(
                    task=task,
                    llm=self.llm
                )

            logger.info(f"✅ VNC agent created successfully on display {display} using {method}")
            return agent

        except Exception as e:
            # Restore original environment on error
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            logger.error(f"Failed to create VNC agent: {e}")
            raise e

    async def execute_task(self, task: str, max_steps: int = 50) -> dict:
        """Execute a single task using browser-use Agent"""
        try:
            logger.info(f"Starting task execution: {task}")
            self.is_running = True
            self.is_stopped = False
            self.is_paused = False

            # Setup VNC if enabled
            await self._setup_vnc_if_enabled()

            # Create agent based on VNC setting
            if self.enable_vnc and self.vnc_server:
                logger.info("Creating VNC-enabled agent")
                # Temporarily set environment for VNC
                original_display = os.environ.get('DISPLAY')
                vnc_env = self.vnc_server.get_display_env()
                os.environ.update(vnc_env)

                try:
                    self.current_agent = await self._create_vnc_agent(task)
                finally:
                    # Restore original display
                    if original_display:
                        os.environ['DISPLAY'] = original_display
                    elif 'DISPLAY' in os.environ:
                        del os.environ['DISPLAY']
            else:
                logger.info("Creating standard agent (PC browser)")
                # Create normal agent (opens in PC browser)
                self.current_agent = Agent(
                    task=task,
                    llm=self.llm
                )

            # Execute the task
            result = await self.current_agent.run(max_steps=max_steps)

            logger.info(f"Task completed successfully: {task}")
            return {
                "status": "completed",
                "task": task,
                "result": str(result),
                "success": True,
                "vnc_info": self.vnc_info if self.enable_vnc else None
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "status": "failed",
                "task": task,
                "error": str(e),
                "success": False,
                "vnc_info": self.vnc_info if self.enable_vnc else None
            }
        finally:
            self.is_running = False
            self.current_agent = None
            # Keep VNC running for potential next task
            # await self._cleanup_vnc()

    async def pause(self):
        """Pause current task execution"""
        if self.current_agent and self.is_running:
            self.is_paused = True
            # Note: browser-use Agent doesn't have direct pause/resume
            # This is a placeholder for future implementation
            logger.info("Task paused")

    async def resume(self):
        """Resume paused task execution"""
        if self.is_paused:
            self.is_paused = False
            logger.info("Task resumed")

    async def stop(self):
        """Stop current task execution"""
        if self.current_agent and self.is_running:
            self.is_stopped = True
            # Note: browser-use Agent doesn't have direct stop method
            # This is a placeholder for future implementation
            logger.info("Task stopped")

    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "is_stopped": self.is_stopped,
            "llm_provider": self.llm_provider,
            "model_name": self.model_name,
            "vnc_enabled": self.enable_vnc,
            "vnc_info": self.vnc_info
        }

    def get_vnc_info(self) -> Optional[Dict]:
        """Get VNC connection information"""
        return self.vnc_info if self.enable_vnc else None

    async def cleanup(self):
        """Cleanup resources including VNC"""
        await self._cleanup_vnc()
