import json
from collections.abc import Generator
from typing import TYPE_CHECKING
import os
import gradio as gr
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
import uuid
import asyncio
import time
from collections import deque

from gradio.components import Component
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.agent.service import Agent
# Temporarily disable problematic imports to get webUI working
# from src.browser.custom_browser import CustomBrowser
# from src.browser.custom_context import CustomBrowserContext
# from src.controller.custom_controller import CustomController
# from src.agent.deep_research.deep_research_agent import DeepResearchAgent


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, Component] = {}
        self.component_to_id: dict[Component, str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # Task queue management attributes
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.current_task_id: Optional[str] = None
        self.current_task_future: Optional[asyncio.Future] = None
        self.task_status: Dict[str, str] = {}
        self.task_descriptions: Dict[str, str] = {}
        self.pause_event: asyncio.Event = asyncio.Event()
        self.stop_event: asyncio.Event = asyncio.Event()
        self.pause_event.set()  # Initially not paused

        # Task processor loop task
        self.task_processor_task: Optional[asyncio.Task] = None

    def init_browser_use_agent(self) -> None:
        """
        init browser use agent
        """
        self.bu_agent: Optional[Agent] = None
        self.bu_browser: Optional[Any] = None  # CustomBrowser temporarily disabled
        self.bu_browser_context: Optional[Any] = None  # CustomBrowserContext temporarily disabled
        self.bu_controller: Optional[Any] = None  # CustomController temporarily disabled
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_response_event: Optional[asyncio.Event] = None
        self.bu_user_help_response: Optional[str] = None
        self.bu_current_task: Optional[asyncio.Task] = None
        self.bu_agent_task_id: Optional[str] = None

    def init_deep_research_agent(self) -> None:
        """
        init deep research agent
        """
        self.dr_agent: Optional[Any] = None  # DeepResearchAgent temporarily disabled

        # VNC settings
        self.vnc_enabled = False
        self.current_vnc_info = None
        self.dr_current_task = None
        self.dr_agent_task_id: Optional[str] = None
        self.dr_save_dir: Optional[str] = None

    def add_components(self, tab_name: str, components_dict: dict[str, "Component"]) -> None:
        """
        Add tab components
        """
        for comp_name, component in components_dict.items():
            comp_id = f"{tab_name}.{comp_name}"
            self.id_to_component[comp_id] = component
            self.component_to_id[component] = comp_id

    def get_components(self) -> list["Component"]:
        """
        Get all components
        """
        return list(self.id_to_component.values())

    def get_component_by_id(self, comp_id: str) -> "Component":
        """
        Get component by id
        """
        return self.id_to_component[comp_id]

    def get_id_by_component(self, comp: "Component") -> str:
        """
        Get id by component
        """
        return self.component_to_id[comp]

    def save_config(self, components: Dict["Component", str]) -> None:
        """
        Save config
        """
        cur_settings = {}
        for comp in components:
            if not isinstance(comp, gr.Button) and not isinstance(comp, gr.File) and str(
                    getattr(comp, "interactive", True)).lower() != "false":
                comp_id = self.get_id_by_component(comp)
                cur_settings[comp_id] = components[comp]

        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(self.settings_save_dir, f"{config_name}.json"), "w") as fw:
            json.dump(cur_settings, fw, indent=4)

        return os.path.join(self.settings_save_dir, f"{config_name}.json")

    def load_config(self, config_path: str):
        """
        Load config
        """
        with open(config_path, "r") as fr:
            ui_settings = json.load(fr)

        update_components = {}
        for comp_id, comp_val in ui_settings.items():
            if comp_id in self.id_to_component:
                comp = self.id_to_component[comp_id]
                if comp.__class__.__name__ == "Chatbot":
                    update_components[comp] = comp.__class__(value=comp_val, type="messages")
                else:
                    update_components[comp] = comp.__class__(value=comp_val)
                    if comp_id == "agent_settings.planner_llm_provider":
                        yield update_components  # yield provider, let callback run
                        time.sleep(0.1)  # wait for Gradio UI callback

        config_status = self.id_to_component["load_save_config.config_status"]
        update_components.update(
            {
                config_status: config_status.__class__(value=f"Successfully loaded config: {config_path}")
            }
        )
        yield update_components

    # Task Queue Management Methods
    async def add_task(self, task_description: str, task_type: str = "browser_use") -> str:
        """Add a new task to the queue."""
        task_id = str(uuid.uuid4())
        task_info = {
            "id": task_id,
            "description": task_description,
            "type": task_type,
            "status": "en cola",
            "timestamp": datetime.now().isoformat()
        }
        await self.task_queue.put(task_info)
        self.task_status[task_id] = "en cola"
        self.task_descriptions[task_id] = task_description
        print(f"Tarea '{task_description}' ({task_id}) añadida a la cola.")
        return task_id

    async def pause_current_task(self):
        """Pause the currently running task."""
        if self.current_task_id and self.task_status.get(self.current_task_id) == "ejecutando":
            self.pause_event.clear()  # Signal pause
            self.task_status[self.current_task_id] = "pausada"
            print(f"Tarea {self.current_task_id} pausada.")
        else:
            print("No hay tarea en ejecución para pausar.")

    async def resume_current_task(self):
        """Resume the currently paused task."""
        if self.current_task_id and self.task_status.get(self.current_task_id) == "pausada":
            self.pause_event.set()  # Signal resume
            self.task_status[self.current_task_id] = "ejecutando"
            print(f"Tarea {self.current_task_id} reanudada.")
        else:
            print("No hay tarea pausada para reanudar.")

    async def stop_task(self, task_id: Optional[str] = None):
        """Stop a specific task or the current task."""
        if task_id is None:  # Stop current task
            if self.current_task_id:
                task_to_stop_id = self.current_task_id
                if self.current_task_future:
                    self.stop_event.set()  # Signal stop
                    # Wait briefly for task to respond to stop signal
                    try:
                        await asyncio.wait_for(self.current_task_future, timeout=1)
                    except asyncio.TimeoutError:
                        print(f"La tarea {task_to_stop_id} no respondió a la señal de detención, cancelando forzosamente.")
                        self.current_task_future.cancel()
                    except asyncio.CancelledError:
                        print(f"La tarea {task_to_stop_id} fue cancelada.")
                    finally:
                        self.task_status[task_to_stop_id] = "detenida"
                        self.current_task_id = None
                        self.current_task_future = None
                        self.stop_event.clear()
                        self.pause_event.set()
                        print(f"Tarea {task_to_stop_id} detenida.")
            else:
                print("No hay tarea en ejecución para detener.")
        else:  # Stop specific task in queue
            if self.task_status.get(task_id) == "en cola":
                self.task_status[task_id] = "detenida"
                print(f"Tarea {task_id} eliminada de la cola.")
            else:
                print(f"La tarea {task_id} no está en cola o en ejecución para detener.")

    async def handle_user_input(self, user_message: str) -> Tuple[str, List[List[str]]]:
        """Handle user input - either control commands or new tasks."""
        user_message_lower = user_message.lower().strip()

        if user_message_lower == "pausar":
            await self.pause_current_task()
            return "Comando de pausa enviado.", self.bu_chat_history
        elif user_message_lower == "reanudar":
            await self.resume_current_task()
            return "Comando de reanudación enviado.", self.bu_chat_history
        elif user_message_lower == "detener":
            await self.stop_task()
            return "Comando de detención enviado.", self.bu_chat_history
        else:
            # Add new task to queue
            task_id = await self.add_task(user_message, task_type="browser_use")
            self.bu_chat_history.append([user_message, f"Tarea añadida a la cola: {user_message} (ID: {task_id[:8]}...)"])
            return "", self.bu_chat_history

    def get_queue_display_text(self) -> str:
        """Get formatted text for task queue display."""
        queue_contents = []
        for task_id, status in self.task_status.items():
            description = self.task_descriptions.get(task_id, "Sin descripción")[:50]
            if status == "en cola":
                queue_contents.append(f"- {description}... ({task_id[:8]}): {status}")
            elif status == "ejecutando":
                queue_contents.append(f"- {description}... ({task_id[:8]}): {status} (Actual)")
            elif status == "pausada":
                queue_contents.append(f"- {description}... ({task_id[:8]}): {status} (Actual)")

        return "\n".join(queue_contents) if queue_contents else "No hay tareas en cola."

    def is_pause_button_active(self) -> bool:
        """Check if pause button should be active."""
        return (self.current_task_id is not None and
                self.task_status.get(self.current_task_id) == "ejecutando")

    def is_stop_button_active(self) -> bool:
        """Check if stop button should be active."""
        return (self.current_task_id is not None and
                self.task_status.get(self.current_task_id) in ["ejecutando", "pausada"])

    async def start_task_processor(self):
        """Start the task processor loop."""
        if self.task_processor_task is None or self.task_processor_task.done():
            self.task_processor_task = asyncio.create_task(self._task_processor_loop())

    async def stop_task_processor(self):
        """Stop the task processor loop."""
        if self.task_processor_task and not self.task_processor_task.done():
            self.task_processor_task.cancel()
            try:
                await self.task_processor_task
            except asyncio.CancelledError:
                pass

    async def _task_processor_loop(self):
        """Main task processor loop that handles tasks from the queue."""
        while True:
            try:
                task_info = await self.task_queue.get()
                task_id = task_info["id"]
                task_description = task_info["description"]
                task_type = task_info["type"]

                if self.task_status.get(task_id) == "detenida":
                    print(f"Saltando tarea detenida: {task_id}")
                    self.task_queue.task_done()
                    continue

                self.current_task_id = task_id
                self.task_status[task_id] = "ejecutando"
                self.stop_event.clear()
                self.pause_event.set()

                print(f"Iniciando tarea: {task_description} ({task_id})")

                try:
                    # Execute actual browser automation task
                    self.current_task_future = asyncio.create_task(
                        self._execute_browser_task(task_id, task_description)
                    )
                    result = await self.current_task_future

                    if self.task_status.get(task_id) != "detenida":
                        if result.get("success", False):
                            self.task_status[task_id] = "completada"
                            print(f"Tarea {task_id} completada exitosamente.")
                        else:
                            self.task_status[task_id] = "fallida"
                            print(f"Tarea {task_id} falló: {result.get('error', 'Error desconocido')}")

                except asyncio.CancelledError:
                    print(f"Tarea {task_id} fue cancelada externamente.")
                    self.task_status[task_id] = "detenida"
                except Exception as e:
                    print(f"Error ejecutando tarea {task_id}: {e}")
                    self.task_status[task_id] = "fallida"
                finally:
                    self.task_queue.task_done()
                    self.current_task_id = None
                    self.current_task_future = None
                    self.stop_event.clear()
                    self.pause_event.set()

            except asyncio.CancelledError:
                print("Task processor loop cancelled.")
                break
            except Exception as e:
                print(f"Error in task processor loop: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing

    async def _execute_browser_task(self, task_id: str, description: str) -> dict:
        """Execute actual browser automation task using BrowserUseAgent."""
        try:
            # Import the browser agent
            from src.agent.browser_use.browser_use_agent import BrowserUseAgent

            # Check browser mode setting from UI
            browser_mode = self.get_browser_mode()
            vnc_enabled = (browser_mode == "vnc")

            # Create agent instance with vision-capable model and VNC support
            agent = BrowserUseAgent(
                llm_provider="openai",
                model_name="gpt-4o",
                enable_vnc=vnc_enabled
            )

            print(f"🖥️ Browser mode: {'VNC Viewer' if vnc_enabled else 'PC Browser'}")

            print(f"🚀 Iniciando ejecución de tarea {task_id}: {description}")

            # Execute the task with browser automation
            result = await agent.execute_task(description, max_steps=20)

            # Check for stop/pause during execution
            if self.stop_event.is_set():
                print(f"Tarea {task_id} detenida por solicitud del usuario.")
                await agent.stop()
                raise asyncio.CancelledError("Tarea detenida por el usuario")

            print(f"✅ Tarea {task_id} completada: {result.get('status', 'unknown')}")
            return result

        except asyncio.CancelledError:
            print(f"❌ Tarea {task_id} fue cancelada.")
            raise
        except Exception as e:
            print(f"❌ Error ejecutando tarea {task_id}: {e}")
            return {
                "status": "failed",
                "task": description,
                "error": str(e),
                "success": False
            }

    def get_browser_mode(self) -> str:
        """Get current browser mode from UI components"""
        try:
            # Try to get browser mode from UI component
            browser_mode_component = self.get_component_by_id("browser_use_agent.browser_mode")
            if browser_mode_component and hasattr(browser_mode_component, 'value'):
                return browser_mode_component.value
        except:
            pass

        # Default to PC browser mode
        return "pc"

    def enable_vnc(self, enabled: bool = True):
        """Enable or disable VNC for browser automation"""
        self.vnc_enabled = enabled
        print(f"VNC {'enabled' if enabled else 'disabled'} for browser automation")

    def get_vnc_info(self):
        """Get current VNC connection information"""
        return self.current_vnc_info

    async def cleanup_vnc(self):
        """Cleanup VNC resources"""
        try:
            from src.vnc.vnc_server import vnc_manager
            await vnc_manager.stop_all_servers()
            self.current_vnc_info = None
            print("VNC resources cleaned up")
        except Exception as e:
            print(f"Error cleaning up VNC: {e}")
