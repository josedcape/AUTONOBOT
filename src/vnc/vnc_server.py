#!/usr/bin/env python3
"""
VNC Server integration for browser automation viewing
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
import socket
import platform
from typing import Optional, Dict, Any

# Try to import psutil, install if missing
try:
    import psutil
except ImportError:
    print("Installing psutil dependency...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

logger = logging.getLogger(__name__)


class VNCServer:
    """VNC Server manager for browser automation viewing"""
    
    def __init__(self, display_number: int = 99, port: int = 5999):
        self.display_number = display_number
        self.port = port
        self.display_name = f":{display_number}"
        self.vnc_process: Optional[subprocess.Popen] = None
        self.xvfb_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.screen_width = 1280
        self.screen_height = 1024
        
    def _find_free_port(self, start_port: int = 5900) -> int:
        """Find a free port for VNC server"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No free ports available for VNC server")
    
    def _find_free_display(self, start_display: int = 99) -> int:
        """Find a free display number"""
        for display in range(start_display, start_display + 100):
            lock_file = f"/tmp/.X{display}-lock"
            if not os.path.exists(lock_file):
                return display
        raise RuntimeError("No free display numbers available")
    
    async def start_server(self) -> Dict[str, Any]:
        """Start VNC server with virtual display"""
        try:
            # Check if running on Windows
            import platform
            if platform.system().lower() == "windows":
                return {
                    "status": "error",
                    "error": "VNC server not supported on Windows. Please use WSL or Docker."
                }

            # Find free port and display
            self.port = self._find_free_port()
            self.display_number = self._find_free_display()
            self.display_name = f":{self.display_number}"

            logger.info(f"Starting VNC server on display {self.display_name}, port {self.port}")

            # Check if Xvfb is available
            try:
                subprocess.run(['which', 'Xvfb'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                return {
                    "status": "error",
                    "error": "Xvfb not found. Please install: sudo apt-get install xvfb"
                }

            # Check if x11vnc is available
            try:
                subprocess.run(['which', 'x11vnc'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                return {
                    "status": "error",
                    "error": "x11vnc not found. Please install: sudo apt-get install x11vnc"
                }

            # Start Xvfb (virtual framebuffer)
            xvfb_cmd = [
                'Xvfb',
                self.display_name,
                '-screen', '0', f'{self.screen_width}x{self.screen_height}x24',
                '-ac',
                '+extension', 'GLX',
                '+render',
                '-noreset'
            ]

            self.xvfb_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for Xvfb to start
            await asyncio.sleep(3)

            # Check if Xvfb started successfully
            if self.xvfb_process.poll() is not None:
                stdout, stderr = self.xvfb_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown Xvfb error"
                return {
                    "status": "error",
                    "error": f"Xvfb failed to start: {error_msg}"
                }

            # Start VNC server (x11vnc)
            vnc_cmd = [
                'x11vnc',
                '-display', self.display_name,
                '-rfbport', str(self.port),
                '-forever',
                '-shared',
                '-nopw',  # No password for simplicity
                '-quiet',
                '-bg'  # Run in background
            ]

            self.vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for VNC server to start
            await asyncio.sleep(3)

            # Check if VNC server started successfully
            if self.vnc_process.poll() is not None:
                stdout, stderr = self.vnc_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown VNC error"
                return {
                    "status": "error",
                    "error": f"VNC server failed to start: {error_msg}"
                }

            self.is_running = True

            logger.info(f"VNC server started successfully on port {self.port}")

            return {
                "status": "success",
                "display": self.display_name,
                "port": self.port,
                "width": self.screen_width,
                "height": self.screen_height,
                "vnc_url": f"localhost:{self.port}"
            }

        except Exception as e:
            logger.error(f"Failed to start VNC server: {e}")
            await self.stop_server()
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def stop_server(self):
        """Stop VNC server and virtual display"""
        try:
            logger.info("Stopping VNC server...")
            
            # Stop VNC process
            if self.vnc_process:
                try:
                    self.vnc_process.terminate()
                    self.vnc_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.vnc_process.kill()
                except Exception as e:
                    logger.warning(f"Error stopping VNC process: {e}")
                self.vnc_process = None
            
            # Stop Xvfb process
            if self.xvfb_process:
                try:
                    self.xvfb_process.terminate()
                    self.xvfb_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.xvfb_process.kill()
                except Exception as e:
                    logger.warning(f"Error stopping Xvfb process: {e}")
                self.xvfb_process = None
            
            # Clean up any remaining processes
            await self._cleanup_processes()
            
            self.is_running = False
            logger.info("VNC server stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping VNC server: {e}")
    
    async def _cleanup_processes(self):
        """Clean up any remaining VNC/Xvfb processes"""
        try:
            # Kill any remaining x11vnc processes on our port
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'x11vnc':
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if str(self.port) in cmdline:
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Kill any remaining Xvfb processes on our display
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'Xvfb':
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if self.display_name in cmdline:
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            logger.warning(f"Error during process cleanup: {e}")
    
    def get_display_env(self) -> Dict[str, str]:
        """Get environment variables for running applications on this display"""
        return {
            "DISPLAY": self.display_name,
            "XAUTHORITY": os.path.expanduser("~/.Xauthority")
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current VNC server status"""
        return {
            "is_running": self.is_running,
            "display": self.display_name if self.is_running else None,
            "port": self.port if self.is_running else None,
            "width": self.screen_width,
            "height": self.screen_height,
            "vnc_url": f"localhost:{self.port}" if self.is_running else None
        }


class VNCManager:
    """Global VNC server manager with cross-platform support"""

    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self.default_server: Optional[Any] = None

    async def get_or_create_server(self, server_id: str = "default"):
        """Get existing server or create new one with appropriate implementation"""
        if server_id not in self.servers:
            # Choose implementation based on operating system
            if platform.system().lower() == "windows":
                # Use simple VNC server for immediate testing and mobile access
                from src.vnc.simple_vnc_server import SimpleVNCServer
                self.servers[server_id] = SimpleVNCServer()
                logger.info("Created Simple VNC server for Windows (immediate testing)")
            else:
                self.servers[server_id] = VNCServer()
                logger.info("Created Linux/macOS VNC server")

            if server_id == "default":
                self.default_server = self.servers[server_id]

        return self.servers[server_id]
    
    async def start_server(self, server_id: str = "default") -> Dict[str, Any]:
        """Start VNC server"""
        server = await self.get_or_create_server(server_id)
        return await server.start_server()
    
    async def stop_server(self, server_id: str = "default"):
        """Stop VNC server"""
        if server_id in self.servers:
            await self.servers[server_id].stop_server()
    
    async def stop_all_servers(self):
        """Stop all VNC servers"""
        for server in self.servers.values():
            await server.stop_server()
        self.servers.clear()
        self.default_server = None
    
    def get_server_status(self, server_id: str = "default") -> Dict[str, Any]:
        """Get server status"""
        if server_id in self.servers:
            return self.servers[server_id].get_status()
        return {"is_running": False}


# Global VNC manager instance
vnc_manager = VNCManager()
