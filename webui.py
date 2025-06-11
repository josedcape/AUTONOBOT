import pdb
import logging
import asyncio

from dotenv import load_dotenv

load_dotenv()
import os
import glob
import asyncio
import argparse
import os

logger = logging.getLogger(__name__)

import gradio as gr

from browser_use.agent.service import Agent
from playwright.async_api import async_playwright
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import (
    BrowserContextConfig,
    BrowserContextWindowSize,
)
from langchain_ollama import ChatOllama
from playwright.async_api import async_playwright
from src.utils.agent_state import AgentState

from src.utils import utils
from src.agent.custom_agent import CustomAgent
from src.browser.custom_browser import CustomBrowser
from src.agent.custom_prompts import CustomSystemPrompt
from src.browser.custom_context import BrowserContextConfig, CustomBrowserContext
from src.controller.custom_controller import CustomController
from gradio.themes import Citrus, Default, Glass, Monochrome, Ocean, Origin, Soft, Base
from src.utils.default_config_settings import default_config, load_config_from_file, save_config_to_file, save_current_config, update_ui_from_config
from src.utils.utils import update_model_dropdown, get_latest_files, capture_screenshot
from src.utils.task_queue import task_queue, TaskStatus
from src.utils.task_processor import task_processor
from src.utils.task_scheduler import task_scheduler
from src.utils.browser_manager import browser_manager, BrowserMode


# Global variables for persistence
_global_browser = None
_global_browser_context = None

# Create the global agent state instance
_global_agent_state = AgentState()

# Task queue management functions
async def add_task_to_queue(task_name, task_description, additional_info="", priority=0):
    """Add a new task to the queue"""
    try:
        task_id = await task_queue.add_task(task_name, task_description, additional_info, priority)
        return f"Tarea '{task_name}' añadida a la cola (ID: {task_id})", get_queue_display()
    except Exception as e:
        return f"Error al añadir tarea: {str(e)}", get_queue_display()

async def remove_task_from_queue(task_id):
    """Remove a task from the queue"""
    try:
        success = await task_queue.remove_task(task_id)
        if success:
            return "Tarea eliminada de la cola", get_queue_display()
        else:
            return "Tarea no encontrada o no se puede eliminar", get_queue_display()
    except Exception as e:
        return f"Error al eliminar tarea: {str(e)}", get_queue_display()

async def update_task_in_queue(task_id, task_name, task_description, additional_info="", priority=0):
    """Update a task in the queue"""
    try:
        success = await task_queue.update_task(task_id, task_name, task_description, additional_info, priority)
        if success:
            return "Tarea actualizada", get_queue_display()
        else:
            return "Tarea no encontrada o no se puede actualizar", get_queue_display()
    except Exception as e:
        return f"Error al actualizar tarea: {str(e)}", get_queue_display()

async def reorder_task_in_queue(task_id, direction):
    """Move a task up or down in the queue"""
    try:
        tasks = task_queue.get_pending_tasks()
        current_pos = None
        for i, task in enumerate(tasks):
            if task['id'] == task_id:
                current_pos = i
                break

        if current_pos is None:
            return "Tarea no encontrada", get_queue_display()

        direction_text = {"up": "arriba", "down": "abajo"}

        if direction == "up" and current_pos > 0:
            new_pos = current_pos - 1
        elif direction == "down" and current_pos < len(tasks) - 1:
            new_pos = current_pos + 1
        else:
            return f"No se puede mover la tarea en esa dirección", get_queue_display()

        success = await task_queue.reorder_task(task_id, new_pos)
        if success:
            return f"Tarea movida {direction_text.get(direction, direction)}", get_queue_display()
        else:
            return "Error al reordenar tarea", get_queue_display()
    except Exception as e:
        return f"Error al reordenar tarea: {str(e)}", get_queue_display()

def get_queue_display():
    """Get formatted queue display"""
    status = task_queue.get_queue_status()
    tasks = task_queue.get_all_tasks()

    if not tasks:
        return "La cola está vacía"

    display_lines = [
        f"📊 Estado de la Cola: {status['pending']} pendientes, {status['running']} ejecutándose, {status['completed']} completadas, {status['failed']} fallidas",
        f"⏸️ Pausada: {'Sí' if status['is_paused'] else 'No'}",
        ""
    ]

    status_translations = {
        'pending': 'pendiente',
        'running': 'ejecutándose',
        'completed': 'completada',
        'failed': 'fallida',
        'paused': 'pausada',
        'cancelled': 'cancelada'
    }

    for i, task in enumerate(tasks, 1):
        status_emoji = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'paused': '⏸️',
            'cancelled': '🚫'
        }.get(task['status'], '❓')

        status_text = status_translations.get(task['status'], task['status'])
        display_lines.append(f"{i}. {status_emoji} {task['name']} ({status_text})")
        if task['status'] == 'running':
            display_lines.append(f"   📝 {task['description'][:100]}...")
        elif task['status'] in ['completed', 'failed'] and task.get('result'):
            display_lines.append(f"   📝 {task['result'][:100]}...")

    return "\n".join(display_lines)

async def start_queue_processing():
    """Start processing the task queue"""
    try:
        if task_processor.is_processing():
            return "La cola ya se está procesando", get_queue_display()

        # Set up the task processor with the agent runner
        task_processor.set_agent_runner(run_browser_agent)

        # Ensure task processor has current configuration
        # This is critical - without this, it uses default OpenAI config
        logger.info("🔧 Actualizando configuración del procesador de tareas...")
        current_config = task_processor._config
        if not current_config or not current_config.get('llm_api_key'):
            logger.warning("⚠️ ¡El procesador de tareas no tiene configuración LLM! Usar valores por defecto puede causar errores de conexión.")
            logger.info(f"Configuración actual: {current_config}")
        else:
            logger.info(f"✅ Procesador de tareas configurado con LLM: {current_config.get('llm_provider', 'desconocido')}")

        # Start processing in background using threading to avoid asyncio conflicts
        import threading
        def start_processor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(task_processor.start_processing())
            except Exception as e:
                logger.error(f"Error en el hilo del procesador de tareas: {e}")
            finally:
                loop.close()

        processor_thread = threading.Thread(target=start_processor, daemon=True)
        processor_thread.start()

        return "Procesamiento de cola iniciado", get_queue_display()
    except Exception as e:
        return f"Error al iniciar la cola: {str(e)}", get_queue_display()

async def stop_queue_processing():
    """Stop processing the task queue"""
    try:
        await task_processor.stop_processing()
        return "Procesamiento de cola detenido", get_queue_display()
    except Exception as e:
        return f"Error al detener la cola: {str(e)}", get_queue_display()

async def pause_queue():
    """Pause the task queue"""
    try:
        await task_queue.pause_queue()
        return "Cola pausada", get_queue_display()
    except Exception as e:
        return f"Error al pausar la cola: {str(e)}", get_queue_display()

async def resume_queue():
    """Resume the task queue"""
    try:
        await task_queue.resume_queue()
        return "Cola reanudada", get_queue_display()
    except Exception as e:
        return f"Error al reanudar la cola: {str(e)}", get_queue_display()

async def clear_completed_tasks():
    """Clear completed and failed tasks"""
    try:
        await task_queue.clear_completed_tasks()
        return "Tareas completadas eliminadas", get_queue_display()
    except Exception as e:
        return f"Error al limpiar tareas: {str(e)}", get_queue_display()

# Wrapper functions for Gradio compatibility
import threading
import concurrent.futures

def run_async_in_thread(coro):
    """Run async function in a separate thread with its own event loop"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()

def add_task_to_queue_sync(task_name, task_description, additional_info="", priority=0):
    """Synchronous wrapper for add_task_to_queue"""
    try:
        return run_async_in_thread(add_task_to_queue(task_name, task_description, additional_info, priority))
    except Exception as e:
        return f"Error al añadir tarea: {str(e)}", get_queue_display()

def remove_task_from_queue_sync(task_id):
    """Synchronous wrapper for remove_task_from_queue"""
    try:
        return run_async_in_thread(remove_task_from_queue(task_id))
    except Exception as e:
        return f"Error al eliminar tarea: {str(e)}", get_queue_display()

def reorder_task_in_queue_sync(task_id, direction):
    """Synchronous wrapper for reorder_task_in_queue"""
    try:
        return run_async_in_thread(reorder_task_in_queue(task_id, direction))
    except Exception as e:
        return f"Error al reordenar tarea: {str(e)}", get_queue_display()

def start_queue_processing_sync():
    """Synchronous wrapper for start_queue_processing"""
    try:
        return run_async_in_thread(start_queue_processing())
    except Exception as e:
        return f"Error al iniciar la cola: {str(e)}", get_queue_display()

def stop_queue_processing_sync():
    """Synchronous wrapper for stop_queue_processing"""
    try:
        return run_async_in_thread(stop_queue_processing())
    except Exception as e:
        return f"Error al detener la cola: {str(e)}", get_queue_display()

def pause_queue_sync():
    """Synchronous wrapper for pause_queue"""
    try:
        return run_async_in_thread(pause_queue())
    except Exception as e:
        return f"Error al pausar la cola: {str(e)}", get_queue_display()

def resume_queue_sync():
    """Synchronous wrapper for resume_queue"""
    try:
        return run_async_in_thread(resume_queue())
    except Exception as e:
        return f"Error al reanudar la cola: {str(e)}", get_queue_display()

def clear_completed_tasks_sync():
    """Synchronous wrapper for clear_completed_tasks"""
    try:
        return run_async_in_thread(clear_completed_tasks())
    except Exception as e:
        return f"Error al limpiar tareas: {str(e)}", get_queue_display()

# ============================================================================
# FUNCIONES AVANZADAS PARA COLA DE TAREAS EN TIEMPO REAL
# ============================================================================

def get_advanced_queue_display():
    """Obtener display avanzado de la cola con HTML estilizado"""
    try:
        status = task_queue.get_queue_status()
        tasks = task_queue.get_all_tasks()

        if not tasks:
            return """
            <div style='background: rgba(26,26,46,0.6); border-radius: 10px; padding: 20px; border: 1px solid rgba(0,245,255,0.2); min-height: 300px;'>
                <div style='text-align: center; color: #888; padding: 50px;'>
                    <h3>📋 No hay tareas en la cola</h3>
                    <p>Añade una nueva tarea para comenzar</p>
                </div>
            </div>
            """

        html_content = """
        <div style='background: rgba(26,26,46,0.6); border-radius: 10px; padding: 15px; border: 1px solid rgba(0,245,255,0.2);'>
        """

        status_colors = {
            'pending': '#ffa500',
            'running': '#00f5ff',
            'completed': '#00ff00',
            'failed': '#ff0000',
            'paused': '#ff00ff',
            'cancelled': '#888888'
        }

        status_icons = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'paused': '⏸️',
            'cancelled': '🚫'
        }

        status_translations = {
            'pending': 'pendiente',
            'running': 'ejecutándose',
            'completed': 'completada',
            'failed': 'fallida',
            'paused': 'pausada',
            'cancelled': 'cancelada'
        }

        for i, task in enumerate(tasks, 1):
            task_status = task.get('status', 'pending')
            color = status_colors.get(task_status, '#888')
            icon = status_icons.get(task_status, '❓')
            status_text = status_translations.get(task_status, task_status)

            # Calcular tiempo estimado o transcurrido
            time_info = ""
            if task_status == 'running':
                time_info = f"<small style='color: #888;'>⏱️ Ejecutándose...</small>"
            elif task_status == 'pending':
                priority = task.get('priority', 0)
                time_info = f"<small style='color: #888;'>🔢 Prioridad: {priority}</small>"
            elif task_status in ['completed', 'failed']:
                time_info = f"<small style='color: #888;'>✓ Finalizada</small>"

            html_content += f"""
            <div style='background: rgba(0,0,0,0.3); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 1.2rem;'>{icon}</span>
                        <strong style='color: {color}; font-size: 1rem;'>{task.get('name', f'Tarea {i}')}</strong>
                        <span style='background: rgba({color[1:3]}, {color[3:5]}, {color[5:7]}, 0.2); color: {color}; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; text-transform: uppercase;'>{status_text}</span>
                    </div>
                    <div style='color: #888; font-size: 0.8rem;'>ID: {task.get('id', 'N/A')}</div>
                </div>
                <div style='color: #e0e0e0; font-size: 0.9rem; margin-bottom: 5px;'>{task.get('description', 'Sin descripción')[:100]}{'...' if len(task.get('description', '')) > 100 else ''}</div>
                {time_info}
            </div>
            """

        html_content += "</div>"
        return html_content

    except Exception as e:
        return f"""
        <div style='background: rgba(255,0,0,0.1); border-radius: 10px; padding: 20px; border: 1px solid rgba(255,0,0,0.3);'>
            <h4 style='color: #ff0000; margin: 0;'>❌ Error al cargar tareas</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>{str(e)}</p>
        </div>
        """

def get_queue_stats_display():
    """Obtener estadísticas de la cola en formato HTML"""
    try:
        status = task_queue.get_queue_status()

        return f"""
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px;'>
            <div style='background: rgba(255,165,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(255,165,0,0.3);'>
                <h4 style='color: #ffa500; margin: 0; font-size: 1.2rem;'>{status['pending']}</h4>
                <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Pendientes</p>
            </div>
            <div style='background: rgba(0,245,255,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(0,245,255,0.3);'>
                <h4 style='color: #00f5ff; margin: 0; font-size: 1.2rem;'>{status['running']}</h4>
                <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Ejecutándose</p>
            </div>
            <div style='background: rgba(0,255,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(0,255,0,0.3);'>
                <h4 style='color: #00ff00; margin: 0; font-size: 1.2rem;'>{status['completed']}</h4>
                <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Completadas</p>
            </div>
            <div style='background: rgba(255,0,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(255,0,0,0.3);'>
                <h4 style='color: #ff0000; margin: 0; font-size: 1.2rem;'>{status['failed']}</h4>
                <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Fallidas</p>
            </div>
        </div>
        """
    except Exception as e:
        return f"<div style='color: #ff0000;'>Error: {str(e)}</div>"

def get_current_task_display():
    """Obtener información de la tarea actual en ejecución"""
    try:
        tasks = task_queue.get_all_tasks()
        running_tasks = [task for task in tasks if task.get('status') == 'running']

        if not running_tasks:
            return """
            <div style='padding: 15px; background: rgba(255,165,0,0.1); border-radius: 10px; border: 1px solid rgba(255,165,0,0.3); margin-top: 10px;'>
                <h4 style='color: #ffa500; margin: 0;'>🔄 Tarea Actual</h4>
                <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Ninguna tarea en ejecución</p>
            </div>
            """

        current_task = running_tasks[0]
        return f"""
        <div style='padding: 15px; background: rgba(0,245,255,0.1); border-radius: 10px; border: 1px solid rgba(0,245,255,0.3); margin-top: 10px;'>
            <h4 style='color: #00f5ff; margin: 0;'>🔄 Ejecutando: {current_task.get('name', 'Tarea sin nombre')}</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.9rem;'>{current_task.get('description', 'Sin descripción')[:80]}{'...' if len(current_task.get('description', '')) > 80 else ''}</p>
            <small style='color: #888;'>ID: {current_task.get('id', 'N/A')} • Prioridad: {current_task.get('priority', 0)}</small>
        </div>
        """
    except Exception as e:
        return f"""
        <div style='padding: 15px; background: rgba(255,0,0,0.1); border-radius: 10px; border: 1px solid rgba(255,0,0,0.3); margin-top: 10px;'>
            <h4 style='color: #ff0000; margin: 0;'>❌ Error</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>{str(e)}</p>
        </div>
        """

def add_advanced_task_to_queue(task_name, task_description, additional_info="", priority=1, execution_mode="Inmediato", delay_preset="5 minutos", delay_minutes=5, scheduled_date="", scheduled_hour="14", scheduled_minute="00"):
    """Añadir tarea avanzada a la cola con opciones de programación mejoradas"""
    try:
        import datetime
        from src.utils.task_scheduler import task_scheduler, ScheduleType

        # Validar y procesar el modo de ejecución
        if execution_mode == "Diferido":
            # Determinar minutos según preset o valor personalizado
            if delay_preset == "Personalizado":
                minutes = delay_minutes
            else:
                preset_minutes = {
                    "5 minutos": 5,
                    "15 minutos": 15,
                    "30 minutos": 30,
                    "1 hora": 60,
                    "2 horas": 120
                }
                minutes = preset_minutes.get(delay_preset, 5)

            # Calcular tiempo de ejecución diferida
            execute_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            additional_info += f"\n[PROGRAMADO PARA: {execute_at.strftime('%Y-%m-%d %H:%M:%S')}]"

            # Usar el programador de tareas
            task_id = run_async_in_thread(task_scheduler.schedule_task(
                task_name, task_description, additional_info, priority,
                ScheduleType.DELAYED, execute_at
            ))

            return f"✅ Tarea '{task_name}' programada para ejecutarse en {delay_preset if delay_preset != 'Personalizado' else f'{delay_minutes} minutos'}", get_advanced_queue_display()

        elif execution_mode == "Programado":
            if not scheduled_date or not scheduled_hour or not scheduled_minute:
                return "❌ Error: Debe completar todos los campos de fecha y hora", get_advanced_queue_display()

            try:
                # Construir fecha/hora programada
                scheduled_datetime_str = f"{scheduled_date} {scheduled_hour}:{scheduled_minute}"
                execute_at = datetime.datetime.strptime(scheduled_datetime_str, "%Y-%m-%d %H:%M")

                if execute_at <= datetime.datetime.now():
                    return "❌ Error: La fecha/hora programada debe ser futura", get_advanced_queue_display()

                additional_info += f"\n[PROGRAMADO PARA: {execute_at.strftime('%Y-%m-%d %H:%M:%S')}]"

                # Usar el programador de tareas
                task_id = run_async_in_thread(task_scheduler.schedule_task(
                    task_name, task_description, additional_info, priority,
                    ScheduleType.SCHEDULED, execute_at
                ))

                return f"✅ Tarea '{task_name}' programada para {scheduled_date} a las {scheduled_hour}:{scheduled_minute}", get_advanced_queue_display()

            except ValueError:
                return "❌ Error: Formato de fecha inválido. Use YYYY-MM-DD", get_advanced_queue_display()

        else:  # Inmediato
            # Usar el programador de tareas para ejecución inmediata
            task_id = run_async_in_thread(task_scheduler.schedule_task(
                task_name, task_description, additional_info, priority,
                ScheduleType.IMMEDIATE
            ))

            return f"✅ Tarea '{task_name}' añadida a la cola para ejecución inmediata", get_advanced_queue_display()

    except Exception as e:
        return f"❌ Error al añadir tarea: {str(e)}", get_advanced_queue_display()

def add_and_start_advanced_task(task_name, task_description, additional_info="", priority=1, execution_mode="Inmediato", delay_preset="5 minutos", delay_minutes=5, scheduled_date="", scheduled_hour="14", scheduled_minute="00"):
    """Añadir tarea avanzada y iniciar la cola"""
    try:
        # Primero añadir la tarea
        message1, _ = add_advanced_task_to_queue(task_name, task_description, additional_info, priority, execution_mode, delay_preset, delay_minutes, scheduled_date, scheduled_hour, scheduled_minute)

        # Luego iniciar la cola si es ejecución inmediata
        if execution_mode == "Inmediato":
            message2, _ = run_async_in_thread(start_queue_processing())
            return f"{message1}\n{message2}", get_advanced_queue_display()
        else:
            return f"{message1}\n⏰ Cola programada - se iniciará automáticamente en el momento indicado", get_advanced_queue_display()

    except Exception as e:
        return f"❌ Error: {str(e)}", get_advanced_queue_display()

def pause_individual_task(task_id):
    """Pausar una tarea individual"""
    try:
        if not task_id:
            return "❌ Error: Debe especificar un ID de tarea", get_advanced_queue_display()

        # Aquí implementarías la lógica para pausar una tarea específica
        # Por ahora, usamos la funcionalidad existente de pausa de cola
        message, _ = run_async_in_thread(pause_queue())
        return f"⏸️ Tarea {task_id}: {message}", get_advanced_queue_display()

    except Exception as e:
        return f"❌ Error al pausar tarea: {str(e)}", get_advanced_queue_display()

def resume_individual_task(task_id):
    """Reanudar una tarea individual"""
    try:
        if not task_id:
            return "❌ Error: Debe especificar un ID de tarea", get_advanced_queue_display()

        # Aquí implementarías la lógica para reanudar una tarea específica
        message, _ = run_async_in_thread(resume_queue())
        return f"▶️ Tarea {task_id}: {message}", get_advanced_queue_display()

    except Exception as e:
        return f"❌ Error al reanudar tarea: {str(e)}", get_advanced_queue_display()

def stop_individual_task(task_id):
    """Detener una tarea individual"""
    try:
        if not task_id:
            return "❌ Error: Debe especificar un ID de tarea", get_advanced_queue_display()

        # Usar la funcionalidad existente de eliminación de tarea
        message, _ = run_async_in_thread(remove_task_from_queue(task_id))
        return f"⏹️ Tarea {task_id}: {message}", get_advanced_queue_display()

    except Exception as e:
        return f"❌ Error al detener tarea: {str(e)}", get_advanced_queue_display()

def update_scheduling_visibility(execution_mode):
    """Actualizar visibilidad de opciones de programación mejoradas"""
    if execution_mode == "Diferido":
        return (
            gr.update(visible=True),   # scheduling_options
            gr.update(visible=True),   # delay_options
            gr.update(visible=False)   # schedule_options
        )
    elif execution_mode == "Programado":
        return (
            gr.update(visible=True),   # scheduling_options
            gr.update(visible=False),  # delay_options
            gr.update(visible=True)    # schedule_options
        )
    else:  # Inmediato
        return (
            gr.update(visible=False),  # scheduling_options
            gr.update(visible=False),  # delay_options
            gr.update(visible=False)   # schedule_options
        )

def update_delay_preset(preset_value):
    """Actualizar campo de minutos según preset seleccionado"""
    preset_minutes = {
        "5 minutos": 5,
        "15 minutos": 15,
        "30 minutos": 30,
        "1 hora": 60,
        "2 horas": 120,
        "Personalizado": 5
    }

    minutes = preset_minutes.get(preset_value, 5)
    show_custom = preset_value == "Personalizado"

    # Calcular tiempo de ejecución
    import datetime
    execute_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    time_str = execute_time.strftime("%H:%M del %d/%m/%Y")

    info_html = f"<div style='color: #00f5ff; font-size: 0.9rem; padding: 10px; background: rgba(0,245,255,0.1); border-radius: 5px; margin-top: 10px;'>📅 Se ejecutará a las: <strong>{time_str}</strong></div>"

    return (
        gr.update(value=minutes, visible=show_custom),
        info_html
    )

def update_schedule_info(date, hour, minute):
    """Actualizar información de programación"""
    try:
        if date and hour and minute:
            info_html = f"<div style='color: #00f5ff; font-size: 0.9rem; padding: 10px; background: rgba(0,245,255,0.1); border-radius: 5px; margin-top: 10px;'>📅 Se ejecutará el: <strong>{date} a las {hour}:{minute}</strong></div>"
        else:
            info_html = "<div style='color: #ffa500; font-size: 0.9rem; padding: 10px; background: rgba(255,165,0,0.1); border-radius: 5px; margin-top: 10px;'>⚠️ Completa todos los campos de fecha y hora</div>"
        return info_html
    except:
        return "<div style='color: #ff0000; font-size: 0.9rem; padding: 10px; background: rgba(255,0,0,0.1); border-radius: 5px; margin-top: 10px;'>❌ Error en formato de fecha/hora</div>"

def get_current_datetime_suggestions():
    """Obtener sugerencias de fecha y hora actuales"""
    import datetime
    now = datetime.datetime.now()

    # Fecha actual
    current_date = now.strftime("%Y-%m-%d")

    # Hora actual + 1
    next_hour = (now + datetime.timedelta(hours=1)).strftime("%H")

    # Minutos redondeados a múltiplo de 5
    current_minute = (now.minute // 5) * 5
    next_minute = f"{current_minute:02d}"

    return current_date, next_hour, next_minute

# ============================================================================
# FUNCIONES PARA GESTIÓN DE MODO HEADLESS Y PROGRAMADOR DE TAREAS
# ============================================================================

def toggle_browser_mode():
    """Cambiar entre modo headless y visible"""
    try:
        current_mode = browser_manager.get_current_mode()
        new_mode = BrowserMode.VISIBLE if current_mode == BrowserMode.HEADLESS else BrowserMode.HEADLESS

        # Cambiar modo de forma asíncrona
        success = run_async_in_thread(browser_manager.switch_mode(new_mode, preserve_context=True))

        if success:
            mode_text = "Headless" if new_mode == BrowserMode.HEADLESS else "Visible"
            return f"✅ Navegador cambiado a modo {mode_text}", get_browser_status_display()
        else:
            return "❌ Error al cambiar modo del navegador", get_browser_status_display()

    except Exception as e:
        return f"❌ Error: {str(e)}", get_browser_status_display()

def get_browser_status_display():
    """Obtener display del estado del navegador"""
    try:
        status = browser_manager.get_browser_status()

        mode_text = "Headless" if status.mode == BrowserMode.HEADLESS else "Visible"
        mode_color = "#9370db" if status.mode == BrowserMode.HEADLESS else "#00f5ff"

        active_text = "Activo" if status.is_active else "Inactivo"
        active_color = "#00ff00" if status.is_active else "#ff0000"

        health_text = "Saludable" if status.is_healthy else "Con problemas"
        health_color = "#00ff00" if status.is_healthy else "#ff0000"

        error_section = ""
        if status.error_message:
            error_section = f"""
            <div style='margin-top: 10px; padding: 10px; background: rgba(255,0,0,0.1); border-radius: 5px; border: 1px solid rgba(255,0,0,0.3);'>
                <strong style='color: #ff0000;'>Error:</strong> <span style='color: #e0e0e0;'>{status.error_message}</span>
            </div>
            """

        return f"""
        <div style='background: rgba(128,0,128,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(128,0,128,0.3);'>
            <h4 style='color: #9370db; margin: 0 0 10px 0;'>📊 Estado del Navegador</h4>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                <div>
                    <strong style='color: #00f5ff;'>Modo:</strong> <span style='color: {mode_color};'>{mode_text}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Estado:</strong> <span style='color: {active_color};'>{active_text}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Salud:</strong> <span style='color: {health_color};'>{health_text}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Contextos:</strong> <span style='color: #e0e0e0;'>{status.context_count}</span>
                </div>
            </div>
            {error_section}
            <div style='margin-top: 10px; font-size: 0.8rem; color: #888;'>
                Última actividad: {status.last_activity or 'N/A'}
            </div>
        </div>
        """

    except Exception as e:
        return f"""
        <div style='background: rgba(255,0,0,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(255,0,0,0.3);'>
            <h4 style='color: #ff0000; margin: 0;'>❌ Error al obtener estado del navegador</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>{str(e)}</p>
        </div>
        """

def get_scheduler_status_display():
    """Obtener display del estado del programador de tareas"""
    try:
        status = task_scheduler.get_scheduler_status()
        scheduled_tasks = task_scheduler.get_pending_scheduled_tasks()

        running_text = "Ejecutándose" if status['is_running'] else "Detenido"
        running_color = "#00ff00" if status['is_running'] else "#ff0000"

        next_execution = ""
        if status['next_execution']:
            import datetime
            next_time = datetime.datetime.fromisoformat(status['next_execution'])
            next_execution = f"<div><strong style='color: #00f5ff;'>Próxima ejecución:</strong> <span style='color: #ffa500;'>{next_time.strftime('%Y-%m-%d %H:%M:%S')}</span></div>"

        return f"""
        <div style='background: rgba(255,165,0,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(255,165,0,0.3);'>
            <h4 style='color: #ffa500; margin: 0 0 10px 0;'>⏰ Estado del Programador</h4>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                <div>
                    <strong style='color: #00f5ff;'>Estado:</strong> <span style='color: {running_color};'>{running_text}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Total programadas:</strong> <span style='color: #e0e0e0;'>{status['total_scheduled']}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Pendientes:</strong> <span style='color: #ffa500;'>{status['pending']}</span>
                </div>
                <div>
                    <strong style='color: #00f5ff;'>Ejecutadas:</strong> <span style='color: #00ff00;'>{status['executed']}</span>
                </div>
            </div>
            {next_execution}
        </div>
        """

    except Exception as e:
        return f"""
        <div style='background: rgba(255,0,0,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(255,0,0,0.3);'>
            <h4 style='color: #ff0000; margin: 0;'>❌ Error al obtener estado del programador</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>{str(e)}</p>
        </div>
        """

def initialize_browser_and_scheduler():
    """Inicializar el navegador y el programador de tareas"""
    try:
        # Configurar validador de navegador para el programador
        task_scheduler.set_browser_validator(browser_manager.is_browser_healthy)

        # Iniciar el programador de tareas
        task_scheduler.start_scheduler()

        return "✅ Sistema de programación inicializado correctamente"

    except Exception as e:
        return f"❌ Error al inicializar sistema: {str(e)}"

def auto_initialize_browser_on_startup(headless_enabled, disable_security_enabled, window_w, window_h):
    """Inicializar automáticamente el navegador al cargar la interfaz"""
    try:
        # Configuración inicial del navegador basada en los valores de la interfaz
        browser_config = {
            'headless': headless_enabled,
            'disable_security': disable_security_enabled,
            'window_w': int(window_w) if window_w else 1280,
            'window_h': int(window_h) if window_h else 720,
            'chrome_path': None
        }

        # Asegurar que el navegador esté listo con la configuración correcta
        success = run_async_in_thread(browser_manager.ensure_browser_ready(browser_config))

        if success:
            mode_text = "headless" if headless_enabled else "visible"
            logger.info(f"🌐 Navegador auto-inicializado en modo {mode_text}")
            return get_enhanced_browser_status_display()
        else:
            logger.warning("⚠️ Error en auto-inicialización del navegador")
            return get_enhanced_browser_status_display()

    except Exception as e:
        logger.error(f"Error en auto-inicialización: {e}")
        return get_enhanced_browser_status_display()

def auto_switch_headless_mode(headless_enabled):
    """Cambiar automáticamente el modo del navegador basado en la configuración"""
    try:
        # Determinar el modo objetivo basado en la configuración
        target_mode = BrowserMode.HEADLESS if headless_enabled else BrowserMode.VISIBLE
        current_mode = browser_manager.get_current_mode()

        # Si ya está en el modo correcto, no hacer nada
        if current_mode == target_mode:
            mode_text = "headless" if target_mode == BrowserMode.HEADLESS else "visible"
            logger.info(f"🔄 Navegador ya está en modo {mode_text}")
            return get_enhanced_browser_status_display()

        # Cambiar modo automáticamente con preservación de contexto
        logger.info(f"🔄 Cambiando automáticamente a modo {'headless' if headless_enabled else 'visible'}")
        success = run_async_in_thread(browser_manager.switch_mode(target_mode, preserve_context=True))

        if success:
            mode_text = "headless" if target_mode == BrowserMode.HEADLESS else "visible"
            logger.info(f"✅ Navegador cambiado automáticamente a modo {mode_text}")

            # Notificar a los callbacks del programador de tareas sobre el cambio
            try:
                task_scheduler._notify_status_callbacks(f"🎭 Navegador cambiado a modo {mode_text} automáticamente")
            except:
                pass  # No es crítico si falla

        else:
            logger.error("❌ Error al cambiar modo automáticamente")

        return get_enhanced_browser_status_display()

    except Exception as e:
        logger.error(f"Error en cambio automático: {e}")
        return get_enhanced_browser_status_display()

def get_seamless_mode_switch_status():
    """Obtener estado del cambio de modo sin interrupciones"""
    try:
        status = browser_manager.get_browser_status()

        # Información específica sobre el cambio de modo
        if browser_manager._is_switching:
            return """
            <div style='background: rgba(255,165,0,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(255,165,0,0.3);'>
                <h4 style='color: #ffa500; margin: 0 0 10px 0;'>🔄 Cambiando Modo del Navegador</h4>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='width: 20px; height: 20px; border: 2px solid #ffa500; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;'></div>
                    <span style='color: #e0e0e0;'>Preservando contexto y cambiando modo...</span>
                </div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
                <div style='margin-top: 10px; font-size: 0.9rem; color: #888;'>
                    • Las tareas en ejecución continuarán sin interrupciones<br>
                    • El contexto del navegador se preservará<br>
                    • La interfaz del Agente Interactivo permanecerá funcional
                </div>
            </div>
            """

        return get_enhanced_browser_status_display()

    except Exception as e:
        return get_enhanced_browser_status_display()

def initialize_browser_with_config(headless_enabled, disable_security_enabled, window_w, window_h, chrome_path=""):
    """Inicializar navegador con configuración específica"""
    try:
        # Crear configuración del navegador
        browser_config = {
            'headless': headless_enabled,
            'disable_security': disable_security_enabled,
            'window_w': int(window_w) if window_w else 1280,
            'window_h': int(window_h) if window_h else 720,
            'chrome_path': chrome_path if chrome_path else None
        }

        # Determinar modo inicial
        initial_mode = BrowserMode.HEADLESS if headless_enabled else BrowserMode.VISIBLE

        # Inicializar navegador con la configuración
        success = run_async_in_thread(browser_manager.initialize_browser(browser_config, force_mode=initial_mode))

        if success:
            mode_text = "headless" if headless_enabled else "visible"
            return f"✅ Navegador inicializado en modo {mode_text}", get_browser_status_display()
        else:
            return "❌ Error al inicializar navegador", get_browser_status_display()

    except Exception as e:
        return f"❌ Error en inicialización: {str(e)}", get_browser_status_display()

def get_mobile_optimized_task_display():
    """Obtener display optimizado para móviles de la cola de tareas"""
    try:
        tasks = task_queue.get_all_tasks()

        if not tasks:
            return """
            <div class="task-card">
                <div class="task-card-header">
                    <h3 class="task-card-title">📋 Cola Vacía</h3>
                </div>
                <p class="task-card-description">No hay tareas en la cola. Añade una nueva tarea para comenzar.</p>
            </div>
            """

        html_content = ""
        for task in tasks[:5]:  # Show only first 5 tasks on mobile
            status_color = {
                "pending": "#ffa500",
                "running": "#00ff00",
                "completed": "#00f5ff",
                "failed": "#ff0000",
                "paused": "#9370db"
            }.get(task.status.value, "#e0e0e0")

            html_content += f"""
            <div class="task-card">
                <div class="task-card-header">
                    <h3 class="task-card-title">{task.name[:30]}...</h3>
                    <span class="task-card-status" style="background: {status_color}20; color: {status_color}; border: 1px solid {status_color};">
                        {task.status.value.upper()}
                    </span>
                </div>
                <p class="task-card-description">{task.description[:100]}...</p>
                <div class="task-card-actions">
                    <span class="task-card-action">📊 Ver</span>
                    <span class="task-card-action">⏸️ Pausar</span>
                    <span class="task-card-action">🗑️ Eliminar</span>
                </div>
            </div>
            """

        if len(tasks) > 5:
            html_content += f"""
            <div class="task-card" style="text-align: center; opacity: 0.7;">
                <p class="task-card-description">... y {len(tasks) - 5} tareas más</p>
            </div>
            """

        return html_content

    except Exception as e:
        return f"""
        <div class="task-card">
            <div class="task-card-header">
                <h3 class="task-card-title">❌ Error</h3>
            </div>
            <p class="task-card-description">Error al cargar tareas: {str(e)}</p>
        </div>
        """

def get_enhanced_browser_status_display():
    """Obtener display mejorado del estado del navegador con información de configuración"""
    try:
        status = browser_manager.get_browser_status()

        mode_text = "Headless" if status.mode == BrowserMode.HEADLESS else "Visible"
        mode_color = "#9370db" if status.mode == BrowserMode.HEADLESS else "#00f5ff"
        mode_icon = "🎭" if status.mode == BrowserMode.HEADLESS else "👁️"

        active_text = "Activo" if status.is_active else "Inactivo"
        active_color = "#00ff00" if status.is_active else "#ff0000"
        active_icon = "✅" if status.is_active else "❌"

        health_text = "Saludable" if status.is_healthy else "Con problemas"
        health_color = "#00ff00" if status.is_healthy else "#ff0000"
        health_icon = "💚" if status.is_healthy else "💔"

        # Información adicional sobre el modo
        mode_info = ""
        if status.mode == BrowserMode.HEADLESS:
            mode_info = """
            <div style='margin-top: 8px; padding: 8px; background: rgba(147,112,219,0.1); border-radius: 5px; border: 1px solid rgba(147,112,219,0.3);'>
                <small style='color: #9370db;'>🎭 Modo Headless Activo</small><br>
                <small style='color: #e0e0e0;'>• Ejecución en segundo plano</small><br>
                <small style='color: #e0e0e0;'>• Optimizado para rendimiento</small><br>
                <small style='color: #e0e0e0;'>• Sin interferencia visual</small>
            </div>
            """
        else:
            mode_info = """
            <div style='margin-top: 8px; padding: 8px; background: rgba(0,245,255,0.1); border-radius: 5px; border: 1px solid rgba(0,245,255,0.3);'>
                <small style='color: #00f5ff;'>👁️ Modo Visible Activo</small><br>
                <small style='color: #e0e0e0;'>• Interfaz gráfica disponible</small><br>
                <small style='color: #e0e0e0;'>• Visualización en tiempo real</small><br>
                <small style='color: #e0e0e0;'>• Ideal para desarrollo</small>
            </div>
            """

        error_section = ""
        if status.error_message:
            error_section = f"""
            <div style='margin-top: 10px; padding: 10px; background: rgba(255,0,0,0.1); border-radius: 5px; border: 1px solid rgba(255,0,0,0.3);'>
                <strong style='color: #ff0000;'>⚠️ Error:</strong> <span style='color: #e0e0e0;'>{status.error_message}</span>
            </div>
            """

        return f"""
        <div style='background: rgba(128,0,128,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(128,0,128,0.3);'>
            <h4 style='color: #9370db; margin: 0 0 15px 0;'>📊 Estado del Navegador en Tiempo Real</h4>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                <div style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;'>
                    <strong style='color: #00f5ff;'>Modo:</strong><br>
                    <span style='color: {mode_color}; font-size: 1.1rem;'>{mode_icon} {mode_text}</span>
                </div>
                <div style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;'>
                    <strong style='color: #00f5ff;'>Estado:</strong><br>
                    <span style='color: {active_color}; font-size: 1.1rem;'>{active_icon} {active_text}</span>
                </div>
                <div style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;'>
                    <strong style='color: #00f5ff;'>Salud:</strong><br>
                    <span style='color: {health_color}; font-size: 1.1rem;'>{health_icon} {health_text}</span>
                </div>
                <div style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;'>
                    <strong style='color: #00f5ff;'>Contextos:</strong><br>
                    <span style='color: #e0e0e0; font-size: 1.1rem;'>🌐 {status.context_count}</span>
                </div>
            </div>
            {mode_info}
            {error_section}
            <div style='margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(128,0,128,0.3); font-size: 0.8rem; color: #888;'>
                <strong>Última actividad:</strong> {status.last_activity or 'N/A'}
            </div>
        </div>
        """

    except Exception as e:
        return f"""
        <div style='background: rgba(255,0,0,0.1); border-radius: 8px; padding: 15px; margin-top: 10px; border: 1px solid rgba(255,0,0,0.3);'>
            <h4 style='color: #ff0000; margin: 0;'>❌ Error al obtener estado del navegador</h4>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>{str(e)}</p>
        </div>
        """

async def ensure_browser_health():
    """Ensure browser and context are healthy and responsive"""
    global _global_browser, _global_browser_context

    try:
        # Check browser health
        if _global_browser and hasattr(_global_browser, '_browser') and _global_browser._browser:
            try:
                await _global_browser._browser.version()
            except Exception:
                logger.info("🔄 Browser not responsive, will recreate")
                await _global_browser.close()
                _global_browser = None
                _global_browser_context = None
                return False

        # Check context health (simplified)
        if _global_browser_context:
            try:
                # Simple check - if context exists, assume it's working
                # More detailed checks will be done when actually using it
                logger.info("🌐 Browser context exists")
                return True
            except Exception:
                logger.info("🔄 Browser context not responsive, will recreate")
                try:
                    await _global_browser_context.close()
                except:
                    pass
                _global_browser_context = None
                return False

        return True
    except Exception as e:
        logger.error(f"Browser health check failed: {e}")
        return False

async def reset_browser_session():
    """Reset the global browser session"""
    global _global_browser, _global_browser_context
    try:
        if _global_browser_context:
            await _global_browser_context.close()
            _global_browser_context = None

        if _global_browser:
            await _global_browser.close()
            _global_browser = None

        return "Sesión del navegador reiniciada exitosamente", get_queue_display()
    except Exception as e:
        return f"Error al reiniciar el navegador: {str(e)}", get_queue_display()

def reset_browser_session_sync():
    """Synchronous wrapper for reset_browser_session"""
    try:
        return run_async_in_thread(reset_browser_session())
    except Exception as e:
        return f"Error al reiniciar el navegador: {str(e)}", get_queue_display()

def force_update_task_processor_config(llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                                     agent_type, use_own_browser, headless, disable_security, window_w, window_h,
                                     save_recording_path, save_agent_history_path, save_trace_path, enable_recording,
                                     max_steps, use_vision, max_actions_per_step, tool_calling_method):
    """Force update task processor configuration with current UI values"""
    try:
        config = {
            'agent_type': agent_type,
            'llm_provider': llm_provider,
            'llm_model_name': llm_model_name,
            'llm_temperature': llm_temperature,
            'llm_base_url': llm_base_url,
            'llm_api_key': llm_api_key,
            'use_own_browser': use_own_browser,
            'headless': headless,
            'disable_security': disable_security,
            'window_w': int(window_w),
            'window_h': int(window_h),
            'save_recording_path': save_recording_path,
            'save_agent_history_path': save_agent_history_path,
            'save_trace_path': save_trace_path,
            'enable_recording': enable_recording,
            'max_steps': int(max_steps),
            'use_vision': use_vision,
            'max_actions_per_step': int(max_actions_per_step),
            'tool_calling_method': tool_calling_method
        }
        task_processor.set_config(config)

        # Log the configuration for debugging
        logger.info(f"🔧 Task processor updated with LLM: {llm_provider}, Model: {llm_model_name}")
        if llm_api_key:
            logger.info(f"✅ API key configured (length: {len(llm_api_key)})")
        else:
            logger.warning("⚠️ No API key configured!")

        return f"✅ Procesador de tareas configurado con {llm_provider} ({llm_model_name})", get_queue_display()
    except Exception as e:
        logger.error(f"Error al actualizar configuración del procesador de tareas: {e}")
        return f"❌ Error al actualizar configuración: {str(e)}", get_queue_display()

def add_and_start_queue_handler_sync(name, desc, info, priority):
    """Synchronous wrapper for add_and_start_queue_handler"""
    try:
        # Add task to queue
        message1, display1 = run_async_in_thread(add_task_to_queue(name, desc, info, priority))
        # Start queue processing
        message2, display2 = run_async_in_thread(start_queue_processing())
        return f"{message1}\n{message2}", display2
    except Exception as e:
        return f"Error: {str(e)}", get_queue_display()

async def stop_agent():
    """Request the agent to stop and update UI with enhanced feedback"""
    global _global_agent_state, _global_browser_context, _global_browser

    try:
        # Request stop
        _global_agent_state.request_stop()

        # Update UI immediately
        message = "Detención solicitada - el agente se detendrá en el siguiente punto seguro"
        logger.info(f"🛑 {message}")

        # Return UI updates
        return (
            message,                                        # errors_output
            gr.update(value="Deteniendo...", interactive=False),  # stop_button
            gr.update(interactive=False),                      # run_button
        )
    except Exception as e:
        error_msg = f"Error durante la detención: {str(e)}"
        logger.error(error_msg)
        return (
            error_msg,
            gr.update(value="Detener", interactive=True),
            gr.update(interactive=True)
        )

async def run_browser_agent(
        agent_type,
        llm_provider,
        llm_model_name,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        enable_recording,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    global _global_agent_state
    _global_agent_state.clear_stop()  # Clear any previous stop requests

    try:
        # Disable recording if the checkbox is unchecked
        if not enable_recording:
            save_recording_path = None

        # Ensure the recording directory exists if recording is enabled
        if save_recording_path:
            os.makedirs(save_recording_path, exist_ok=True)

        # Get the list of existing videos before the agent runs
        existing_videos = set()
        if save_recording_path:
            existing_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )

        # Run the agent
        llm = utils.get_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            temperature=llm_temperature,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        if agent_type == "org":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_org_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        elif agent_type == "custom":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_custom_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                add_infos=add_infos,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")

        # Get the list of videos after the agent runs (if recording is enabled)
        latest_video = None
        if save_recording_path:
            new_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )
            if new_videos - existing_videos:
                latest_video = list(new_videos - existing_videos)[0]  # Get the first new video

        return (
            final_result,
            errors,
            model_actions,
            model_thoughts,
            latest_video,
            trace_file,
            history_file,
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return (
            '',                                         # final_result
            errors,                                     # errors
            '',                                         # model_actions
            '',                                         # model_thoughts
            None,                                       # latest_video
            None,                                       # history_file
            None,                                       # trace_file
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )


async def run_org_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state
        
        # Clear any previous stop request
        _global_agent_state.clear_stop()

        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
        else:
            chrome_path = None

        if _global_browser is None:
            _global_browser = Browser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=[f"--window-size={window_w},{window_h}"],
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(
                        width=window_w, height=window_h
                    ),
                )
            )
            
        agent = Agent(
            task=task,
            llm=llm,
            use_vision=use_vision,
            browser=_global_browser,
            browser_context=_global_browser_context,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        # For queue processing, always keep browser open
        if not keep_browser_open and not task_processor.is_processing():
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_custom_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state

        # Clear any previous stop request
        _global_agent_state.clear_stop()

        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
        else:
            chrome_path = None

        controller = CustomController()

        # Check browser health before proceeding
        browser_healthy = await ensure_browser_health()
        if not browser_healthy:
            logger.info("🔄 Browser health check failed, will recreate")

        # Initialize global browser if needed or if it's closed
        if _global_browser is None:
            logger.info("🌐 Creating new browser instance...")
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=[
                        f"--window-size={window_w},{window_h}",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding"
                    ],
                )
            )
        else:
            # Check if browser is still alive
            try:
                # Try to access browser to verify it's still running
                if hasattr(_global_browser, '_browser') and _global_browser._browser:
                    # Try to get browser version to verify it's alive
                    try:
                        await _global_browser._browser.version()
                        logger.info("🌐 Browser is alive and responsive")
                    except Exception:
                        # Browser is not responsive, recreate
                        logger.info("🔄 Browser not responsive, recreating...")
                        await _global_browser.close()
                        _global_browser = CustomBrowser(
                            config=BrowserConfig(
                                headless=headless,
                                disable_security=disable_security,
                                chrome_instance_path=chrome_path,
                                extra_chromium_args=[
                                    f"--window-size={window_w},{window_h}",
                                    "--no-sandbox",
                                    "--disable-dev-shm-usage",
                                    "--disable-gpu",
                                    "--disable-web-security",
                                    "--disable-features=VizDisplayCompositor",
                                    "--disable-background-timer-throttling",
                                    "--disable-backgrounding-occluded-windows",
                                    "--disable-renderer-backgrounding"
                                ],
                            )
                        )
                        _global_browser_context = None  # Reset context too
                else:
                    # Browser is dead, recreate
                    logger.info("🔄 Browser is dead, recreating...")
                    _global_browser = CustomBrowser(
                        config=BrowserConfig(
                            headless=headless,
                            disable_security=disable_security,
                            chrome_instance_path=chrome_path,
                            extra_chromium_args=[
                                f"--window-size={window_w},{window_h}",
                                "--no-sandbox",
                                "--disable-dev-shm-usage",
                                "--disable-gpu",
                                "--disable-web-security",
                                "--disable-features=VizDisplayCompositor",
                                "--disable-background-timer-throttling",
                                "--disable-backgrounding-occluded-windows",
                                "--disable-renderer-backgrounding"
                            ],
                        )
                    )
                    _global_browser_context = None  # Reset context too
            except Exception as e:
                logger.info(f"🔄 Browser check failed, recreating: {e}")
                try:
                    await _global_browser.close()
                except:
                    pass
                _global_browser = CustomBrowser(
                    config=BrowserConfig(
                        headless=headless,
                        disable_security=disable_security,
                        chrome_instance_path=chrome_path,
                        extra_chromium_args=[
                            f"--window-size={window_w},{window_h}",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                            "--disable-background-timer-throttling",
                            "--disable-backgrounding-occluded-windows",
                            "--disable-renderer-backgrounding"
                        ],
                    )
                )
                _global_browser_context = None  # Reset context too

        if _global_browser_context is None:
            logger.info("🌐 Creating new browser context...")
            try:
                _global_browser_context = await _global_browser.new_context(
                    config=BrowserContextConfig(
                        trace_path=save_trace_path if save_trace_path else None,
                        save_recording_path=save_recording_path if save_recording_path else None,
                        no_viewport=False,
                        browser_window_size=BrowserContextWindowSize(
                            width=window_w, height=window_h
                        ),
                    )
                )

                # Context created successfully
                logger.info("🌐 Browser context created successfully")

            except Exception as e:
                logger.error(f"❌ Failed to create browser context: {e}")
                raise e
        else:
            # Context already exists, assume it's working
            logger.info("🌐 Browser context already exists, reusing")
            
        # Create and run agent
        logger.info("🤖 Creating agent...")
        agent = CustomAgent(
            task=task,
            add_infos=add_infos,
            use_vision=use_vision,
            llm=llm,
            browser=_global_browser,
            browser_context=_global_browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            max_actions_per_step=max_actions_per_step,
            agent_state=_global_agent_state,
            tool_calling_method=tool_calling_method
        )

        # Small delay to ensure browser is fully initialized
        await asyncio.sleep(1)

        logger.info("🚀 Starting agent execution...")
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)        

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()

        # Check if it's a browser-related error
        error_str = str(e)
        if any(keyword in error_str for keyword in ["Browser closed", "TargetClosedError", "Target page", "browser has been closed"]):
            logger.error(f"🔄 Browser error detected: {error_str}")
            # Reset browser state
            _global_browser = None
            _global_browser_context = None
            errors = f"Browser error (will reset for next task): {error_str}"
        else:
            errors = str(e) + "\n" + traceback.format_exc()

        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        # For queue processing, always keep browser open
        if not keep_browser_open and not task_processor.is_processing():
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_with_stream(
    agent_type,
    llm_provider,
    llm_model_name,
    llm_temperature,
    llm_base_url,
    llm_api_key,
    use_own_browser,
    keep_browser_open,
    headless,
    disable_security,
    window_w,
    window_h,
    save_recording_path,
    save_agent_history_path,
    save_trace_path,
    enable_recording,
    task,
    add_infos,
    max_steps,
    use_vision,
    max_actions_per_step,
    tool_calling_method
):
    global _global_agent_state
    stream_vw = 80
    stream_vh = int(80 * window_h // window_w)
    if not headless:
        result = await run_browser_agent(
            agent_type=agent_type,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_temperature=llm_temperature,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            use_own_browser=use_own_browser,
            keep_browser_open=keep_browser_open,
            headless=headless,
            disable_security=disable_security,
            window_w=window_w,
            window_h=window_h,
            save_recording_path=save_recording_path,
            save_agent_history_path=save_agent_history_path,
            save_trace_path=save_trace_path,
            enable_recording=enable_recording,
            task=task,
            add_infos=add_infos,
            max_steps=max_steps,
            use_vision=use_vision,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        # Add HTML content at the start of the result array
        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Usando navegador...</h1>"
        yield [html_content] + list(result)
    else:
        try:
            _global_agent_state.clear_stop()
            # Run the browser agent in the background
            agent_task = asyncio.create_task(
                run_browser_agent(
                    agent_type=agent_type,
                    llm_provider=llm_provider,
                    llm_model_name=llm_model_name,
                    llm_temperature=llm_temperature,
                    llm_base_url=llm_base_url,
                    llm_api_key=llm_api_key,
                    use_own_browser=use_own_browser,
                    keep_browser_open=keep_browser_open,
                    headless=headless,
                    disable_security=disable_security,
                    window_w=window_w,
                    window_h=window_h,
                    save_recording_path=save_recording_path,
                    save_agent_history_path=save_agent_history_path,
                    save_trace_path=save_trace_path,
                    enable_recording=enable_recording,
                    task=task,
                    add_infos=add_infos,
                    max_steps=max_steps,
                    use_vision=use_vision,
                    max_actions_per_step=max_actions_per_step,
                    tool_calling_method=tool_calling_method
                )
            )

            # Initialize values for streaming
            html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Usando navegador...</h1>"
            final_result = errors = model_actions = model_thoughts = ""
            latest_videos = trace = history_file = None


            # Periodically update the stream while the agent task is running
            while not agent_task.done():
                try:
                    encoded_screenshot = await capture_screenshot(_global_browser_context)
                    if encoded_screenshot is not None:
                        html_content = f'<img src="data:image/jpeg;base64,{encoded_screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Esperando sesión del navegador...</h1>"
                except Exception as e:
                    html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Esperando sesión del navegador...</h1>"

                if _global_agent_state and _global_agent_state.is_stop_requested():
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Deteniendo...", interactive=False),  # stop_button
                        gr.update(interactive=False),  # run_button
                    ]
                    break
                else:
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Detener", interactive=True),  # Re-enable stop button
                        gr.update(interactive=True)  # Re-enable run button
                    ]
                await asyncio.sleep(0.05)

            # Once the agent task completes, get the results
            try:
                result = await agent_task
                final_result, errors, model_actions, model_thoughts, latest_videos, trace, history_file, stop_button, run_button = result
            except Exception as e:
                errors = f"Error del agente: {str(e)}"

            yield [
                html_content,
                final_result,
                errors,
                model_actions,
                model_thoughts,
                latest_videos,
                trace,
                history_file,
                stop_button,
                run_button
            ]

        except Exception as e:
            import traceback
            yield [
                f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Esperando sesión del navegador...</h1>",
                "",
                f"Error: {str(e)}\n{traceback.format_exc()}",
                "",
                "",
                None,
                None,
                None,
                gr.update(value="Detener", interactive=True),  # Re-enable stop button
                gr.update(interactive=True)    # Re-enable run button
            ]

# Define the theme map globally
theme_map = {
    "Default": Default(),
    "Soft": Soft(),
    "Monochrome": Monochrome(),
    "Glass": Glass(),
    "Origin": Origin(),
    "Citrus": Citrus(),
    "Ocean": Ocean(),
    "Base": Base()
}

async def close_global_browser():
    global _global_browser, _global_browser_context

    if _global_browser_context:
        await _global_browser_context.close()
        _global_browser_context = None

    if _global_browser:
        await _global_browser.close()
        _global_browser = None

def create_ui(config, theme_name="Ocean"):
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

    /* ============================================================================
       RESPONSIVE DESIGN - MOBILE COMPATIBILITY
       ============================================================================ */

    .gradio-container {
        max-width: 1400px !important;
        margin: auto !important;
        padding-top: 20px !important;
        padding-bottom: 80px !important;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%) !important;
        min-height: 100vh;
    }

    /* Mobile Responsive Breakpoints */
    @media screen and (max-width: 768px) {
        .gradio-container {
            max-width: 100% !important;
            padding: 10px !important;
            padding-bottom: 120px !important; /* Extra space for FABs */
        }
    }

    @media screen and (max-width: 480px) {
        .gradio-container {
            padding: 5px !important;
            padding-bottom: 140px !important;
        }
    }

    .header-text {
        text-align: center;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 30%, #0f3460 70%, #533483 100%);
        padding: 40px 30px;
        border-radius: 25px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0,245,255,0.2);
    }

    /* Mobile Header Responsive */
    @media screen and (max-width: 768px) {
        .header-text {
            margin-bottom: 20px;
            padding: 25px 15px;
            border-radius: 15px;
        }
    }

    @media screen and (max-width: 480px) {
        .header-text {
            margin-bottom: 15px;
            padding: 20px 10px;
            border-radius: 10px;
        }
    }

    .header-text::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(0,245,255,0.1) 50%, transparent 70%);
        animation: shine 4s infinite;
    }

    .header-text::after {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff00, #ffff00);
        background-size: 400% 400%;
        border-radius: 27px;
        z-index: -1;
        animation: gradientShift 6s ease-in-out infinite;
        opacity: 0.3;
    }

    @keyframes shine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .autonobot-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 4rem !important;
        font-weight: 900 !important;
        background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff00, #ffff00);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease-in-out infinite;
        text-shadow: 0 0 30px rgba(0,245,255,0.5);
        margin-bottom: 15px !important;
        letter-spacing: 4px;
        position: relative;
        z-index: 2;
    }

    /* Mobile Title Responsive */
    @media screen and (max-width: 768px) {
        .autonobot-title {
            font-size: 2.5rem !important;
            letter-spacing: 2px;
            margin-bottom: 10px !important;
        }
    }

    @media screen and (max-width: 480px) {
        .autonobot-title {
            font-size: 2rem !important;
            letter-spacing: 1px;
            margin-bottom: 8px !important;
        }
    }

    .autonobot-subtitle {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 300 !important;
        color: #e0e0e0 !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin: 15px 0 !important;
        text-shadow: 0 0 15px rgba(224,224,224,0.4);
        position: relative;
        z-index: 2;
    }

    .status-indicators {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
        flex-wrap: wrap;
        position: relative;
        z-index: 2;
    }

    .status-badge {
        background: rgba(0,245,255,0.1);
        border: 1px solid rgba(0,245,255,0.3);
        border-radius: 20px;
        padding: 8px 16px;
        font-family: 'Exo 2', sans-serif;
        font-size: 0.85rem;
        font-weight: 400;
        color: #00f5ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,245,255,0.2);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.8; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .footer-text {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #00f5ff;
        text-align: center;
        padding: 15px;
        font-family: 'Exo 2', sans-serif;
        font-size: 0.9rem;
        font-weight: 400;
        letter-spacing: 1px;
        border-top: 2px solid rgba(0,245,255,0.3);
        box-shadow: 0 -5px 20px rgba(0,0,0,0.5);
        z-index: 1000;
        text-shadow: 0 0 10px rgba(0,245,255,0.3);
    }

    /* Estilos para las pestañas */
    .tab-nav {
        background: rgba(26,26,46,0.8) !important;
        border-radius: 15px !important;
        padding: 5px !important;
        margin-bottom: 20px !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(0,245,255,0.2) !important;
    }

    .tab-nav button {
        background: transparent !important;
        border: 1px solid rgba(0,245,255,0.2) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 500 !important;
        padding: 12px 20px !important;
        margin: 2px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .tab-nav button:hover {
        background: rgba(0,245,255,0.1) !important;
        border-color: rgba(0,245,255,0.4) !important;
        color: #00f5ff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(0,245,255,0.2) !important;
    }

    .tab-nav button.selected {
        background: linear-gradient(135deg, rgba(0,245,255,0.2), rgba(255,0,255,0.2)) !important;
        border-color: #00f5ff !important;
        color: #00f5ff !important;
        box-shadow: 0 0 20px rgba(0,245,255,0.3) !important;
    }

    /* Estilos para grupos y contenedores */
    .gr-group {
        background: rgba(26,26,46,0.6) !important;
        border: 1px solid rgba(0,245,255,0.2) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin: 10px 0 !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
    }

    /* Estilos para botones */
    .gr-button {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        border: 1px solid rgba(0,245,255,0.3) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .gr-button:hover {
        background: linear-gradient(135deg, rgba(0,245,255,0.2), rgba(255,0,255,0.2)) !important;
        border-color: #00f5ff !important;
        color: #00f5ff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,245,255,0.3) !important;
    }

    .gr-button.primary {
        background: linear-gradient(135deg, #00f5ff, #0080ff) !important;
        border-color: #00f5ff !important;
        color: #000 !important;
        font-weight: 600 !important;
    }

    .gr-button.primary:hover {
        background: linear-gradient(135deg, #00d4ff, #0066cc) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 30px rgba(0,245,255,0.4) !important;
    }

    .theme-section {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 10px;
    }

    /* ============================================================================
       FLOATING ACTION BUTTONS (FAB) - MOBILE SPECIFIC
       ============================================================================ */

    .fab-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        display: none; /* Hidden by default, shown on mobile */
    }

    .fab-main {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00f5ff, #0080ff);
        border: none;
        box-shadow: 0 8px 25px rgba(0,245,255,0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: #000;
        transition: all 0.3s ease;
        position: relative;
    }

    .fab-main:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 35px rgba(0,245,255,0.6);
    }

    .fab-secondary {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, rgba(0,245,255,0.9), rgba(255,0,255,0.9));
        border: 1px solid rgba(0,245,255,0.3);
        box-shadow: 0 6px 20px rgba(0,245,255,0.3);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        color: #fff;
        transition: all 0.3s ease;
        margin-bottom: 10px;
        opacity: 0;
        transform: scale(0);
        backdrop-filter: blur(10px);
    }

    .fab-secondary.show {
        opacity: 1;
        transform: scale(1);
    }

    .fab-secondary:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 25px rgba(0,245,255,0.5);
    }

    /* Mobile FAB Display */
    @media screen and (max-width: 768px) {
        .fab-container {
            display: block;
        }

        .fab-container.expanded .fab-secondary {
            opacity: 1;
            transform: scale(1);
        }

        .fab-container.expanded .fab-secondary:nth-child(2) { transition-delay: 0.1s; }
        .fab-container.expanded .fab-secondary:nth-child(3) { transition-delay: 0.2s; }
        .fab-container.expanded .fab-secondary:nth-child(4) { transition-delay: 0.3s; }
        .fab-container.expanded .fab-secondary:nth-child(5) { transition-delay: 0.4s; }
    }

    /* ============================================================================
       MOBILE RESPONSIVE COMPONENTS
       ============================================================================ */

    /* Touch-Friendly Controls */
    @media screen and (max-width: 768px) {
        .gr-button {
            min-height: 44px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
        }

        .gr-checkbox {
            min-height: 44px !important;
        }

        .gr-dropdown {
            min-height: 44px !important;
        }

        .gr-textbox {
            min-height: 44px !important;
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
    }

    /* Mobile Tabs */
    @media screen and (max-width: 768px) {
        .tab-nav {
            padding: 3px !important;
            margin-bottom: 15px !important;
        }

        .tab-nav button {
            padding: 8px 12px !important;
            font-size: 12px !important;
            margin: 1px !important;
        }
    }

    /* Mobile Groups and Containers */
    @media screen and (max-width: 768px) {
        .gr-group {
            padding: 15px !important;
            margin: 8px 0 !important;
            border-radius: 10px !important;
        }
    }

    @media screen and (max-width: 480px) {
        .gr-group {
            padding: 10px !important;
            margin: 5px 0 !important;
            border-radius: 8px !important;
        }
    }

    /* Mobile Status Indicators */
    @media screen and (max-width: 768px) {
        .status-indicators {
            gap: 10px;
            margin-top: 15px;
        }

        .status-badge {
            padding: 6px 12px;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }
    }

    @media screen and (max-width: 480px) {
        .status-indicators {
            gap: 8px;
            margin-top: 10px;
        }

        .status-badge {
            padding: 4px 8px;
            font-size: 0.7rem;
            letter-spacing: 0px;
        }
    }

    /* ============================================================================
       MOBILE COLLAPSIBLE SECTIONS
       ============================================================================ */

    .mobile-collapsible {
        display: none;
    }

    @media screen and (max-width: 768px) {
        .mobile-collapsible {
            display: block;
        }

        .collapsible-header {
            background: rgba(0,245,255,0.1);
            border: 1px solid rgba(0,245,255,0.3);
            border-radius: 10px;
            padding: 12px 16px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }

        .collapsible-header:hover {
            background: rgba(0,245,255,0.2);
        }

        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .collapsible-content.expanded {
            max-height: 1000px;
        }
    }

    /* ============================================================================
       MOBILE TASK QUEUE CARDS
       ============================================================================ */

    @media screen and (max-width: 768px) {
        .task-card {
            background: rgba(26,26,46,0.8);
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .task-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .task-card-title {
            font-family: 'Exo 2', sans-serif;
            font-weight: 600;
            color: #00f5ff;
            font-size: 1rem;
            margin: 0;
        }

        .task-card-status {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .task-card-description {
            color: #e0e0e0;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-bottom: 10px;
        }

        .task-card-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .task-card-action {
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(0,245,255,0.3);
            background: rgba(0,245,255,0.1);
            color: #00f5ff;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .task-card-action:hover {
            background: rgba(0,245,255,0.2);
            transform: translateY(-1px);
        }
    }
    """

    js = """
    function refresh() {
        const url = new URL(window.location);
        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }

    // ============================================================================
    // MOBILE COMPATIBILITY JAVASCRIPT
    // ============================================================================

    // Initialize mobile features when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeMobileFeatures();
        createFloatingActionButtons();
        setupSwipeGestures();
        setupMobileCollapsibles();
    });

    function initializeMobileFeatures() {
        // Detect mobile device
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            document.body.classList.add('mobile-device');

            // Add viewport meta tag if not present
            if (!document.querySelector('meta[name="viewport"]')) {
                const viewport = document.createElement('meta');
                viewport.name = 'viewport';
                viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                document.head.appendChild(viewport);
            }

            // Prevent zoom on input focus (iOS)
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.style.fontSize = '16px';
            });
        }
    }

    function createFloatingActionButtons() {
        if (window.innerWidth > 768) return; // Only on mobile

        // Create FAB container
        const fabContainer = document.createElement('div');
        fabContainer.className = 'fab-container';
        fabContainer.id = 'fab-container';

        // Create secondary FABs
        const fabButtons = [
            { icon: '⏸️', title: 'Pausar/Reanudar Cola', action: 'toggleQueue' },
            { icon: '🎭', title: 'Cambiar Modo Navegador', action: 'toggleBrowserMode' },
            { icon: '➕', title: 'Añadir Tarea Rápida', action: 'quickAddTask' },
            { icon: '📊', title: 'Estado del Sistema', action: 'showStatus' }
        ];

        // Create secondary FABs
        fabButtons.forEach((btn, index) => {
            const fabSecondary = document.createElement('button');
            fabSecondary.className = 'fab-secondary';
            fabSecondary.innerHTML = btn.icon;
            fabSecondary.title = btn.title;
            fabSecondary.onclick = () => handleFabAction(btn.action);
            fabContainer.appendChild(fabSecondary);
        });

        // Create main FAB
        const fabMain = document.createElement('button');
        fabMain.className = 'fab-main';
        fabMain.innerHTML = '🤖';
        fabMain.title = 'Agente Interactivo';
        fabMain.onclick = toggleFabMenu;
        fabContainer.appendChild(fabMain);

        document.body.appendChild(fabContainer);
    }

    function toggleFabMenu() {
        const fabContainer = document.getElementById('fab-container');
        fabContainer.classList.toggle('expanded');
    }

    function handleFabAction(action) {
        switch(action) {
            case 'toggleQueue':
                // Find and click pause/resume button
                const pauseBtn = document.querySelector('[data-testid*="pause"]') ||
                                document.querySelector('button:contains("Pausar")') ||
                                document.querySelector('button:contains("Reanudar")');
                if (pauseBtn) pauseBtn.click();
                break;

            case 'toggleBrowserMode':
                // Find and click browser mode toggle
                const modeBtn = document.querySelector('button:contains("Cambiar Modo")');
                if (modeBtn) modeBtn.click();
                break;

            case 'quickAddTask':
                // Navigate to Interactive Agent tab
                const agentTab = document.querySelector('[data-testid*="tab"]:contains("Agente Interactivo")') ||
                               document.querySelector('button:contains("🤖")');
                if (agentTab) agentTab.click();
                break;

            case 'showStatus':
                // Show mobile status modal
                showMobileStatusModal();
                break;
        }

        // Close FAB menu after action
        toggleFabMenu();
    }

    function setupSwipeGestures() {
        if (window.innerWidth > 768) return; // Only on mobile

        let startX = 0;
        let startY = 0;

        document.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        document.addEventListener('touchend', function(e) {
            if (!startX || !startY) return;

            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;

            const diffX = startX - endX;
            const diffY = startY - endY;

            // Horizontal swipe detection
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0) {
                    // Swipe left - next tab
                    navigateTab('next');
                } else {
                    // Swipe right - previous tab
                    navigateTab('prev');
                }
            }

            startX = 0;
            startY = 0;
        });
    }

    function navigateTab(direction) {
        const tabs = document.querySelectorAll('[data-testid*="tab"]');
        const activeTab = document.querySelector('[data-testid*="tab"].selected') ||
                         document.querySelector('[data-testid*="tab"][aria-selected="true"]');

        if (!activeTab || tabs.length === 0) return;

        const currentIndex = Array.from(tabs).indexOf(activeTab);
        let newIndex;

        if (direction === 'next') {
            newIndex = (currentIndex + 1) % tabs.length;
        } else {
            newIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        }

        tabs[newIndex].click();
    }

    function setupMobileCollapsibles() {
        if (window.innerWidth > 768) return; // Only on mobile

        // Convert complex sections to collapsibles
        const sections = document.querySelectorAll('.gr-group');
        sections.forEach((section, index) => {
            if (section.children.length > 3) { // Only for complex sections
                const header = document.createElement('div');
                header.className = 'collapsible-header';
                header.innerHTML = `
                    <span>Sección ${index + 1}</span>
                    <span>▼</span>
                `;

                const content = document.createElement('div');
                content.className = 'collapsible-content';

                // Move section content to collapsible
                while (section.firstChild) {
                    content.appendChild(section.firstChild);
                }

                header.onclick = () => {
                    content.classList.toggle('expanded');
                    const arrow = header.querySelector('span:last-child');
                    arrow.textContent = content.classList.contains('expanded') ? '▲' : '▼';
                };

                section.appendChild(header);
                section.appendChild(content);
                section.classList.add('mobile-collapsible');
            }
        });
    }

    function showMobileStatusModal() {
        // Create mobile status modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(0,245,255,0.3);
            border-radius: 15px;
            padding: 20px;
            max-width: 90%;
            max-height: 80%;
            overflow-y: auto;
            color: #e0e0e0;
        `;

        content.innerHTML = `
            <h3 style="color: #00f5ff; margin: 0 0 15px 0;">📊 Estado del Sistema</h3>
            <div id="mobile-status-content">Cargando...</div>
            <button onclick="this.closest('.modal').remove()"
                    style="margin-top: 15px; padding: 10px 20px; background: #00f5ff;
                           border: none; border-radius: 5px; color: #000; cursor: pointer;">
                Cerrar
            </button>
        `;

        modal.className = 'modal';
        modal.appendChild(content);
        document.body.appendChild(modal);

        // Load status content
        updateMobileStatusContent();
    }

    function updateMobileStatusContent() {
        const statusContent = document.getElementById('mobile-status-content');
        if (!statusContent) return;

        // Get status from existing displays
        const browserStatus = document.querySelector('[id*="browser-status"]');
        const queueStatus = document.querySelector('[id*="queue-status"]');

        let content = '<div style="display: grid; gap: 15px;">';

        if (browserStatus) {
            content += `<div><h4 style="color: #9370db;">🌐 Navegador</h4>${browserStatus.innerHTML}</div>`;
        }

        if (queueStatus) {
            content += `<div><h4 style="color: #ffa500;">📋 Cola de Tareas</h4>${queueStatus.innerHTML}</div>`;
        }

        content += '</div>';
        statusContent.innerHTML = content;
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        const isMobile = window.innerWidth <= 768;
        const fabContainer = document.getElementById('fab-container');

        if (isMobile && !fabContainer) {
            createFloatingActionButtons();
        } else if (!isMobile && fabContainer) {
            fabContainer.remove();
        }
    });
    """

    with gr.Blocks(
            title="AUTONOBOT - Agente de Navegación Autónoma", theme=theme_map[theme_name], css=css, js=js
    ) as demo:
        with gr.Row():
            gr.HTML(
                """
                <div class="header-text">
                    <h1 class="autonobot-title">🛡️ AUTONOBOT</h1>
                    <h3 class="autonobot-subtitle">AGENTE DE NAVEGACIÓN AUTÓNOMA</h3>
                    <div class="status-indicators">
                        <div class="status-badge">● CHAT INTERACTIVO LISTO</div>
                        <div class="status-badge">● SOPORTE MULTI-TAREA</div>
                        <div class="status-badge">● CONTROL EN TIEMPO REAL</div>
                    </div>
                </div>
                """,
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("⚙️ Configuración del Agente", id=1):
                with gr.Group():
                    agent_type = gr.Radio(
                        ["org", "custom"],
                        label="Tipo de Agente",
                        value=config['agent_type'],
                        info="Selecciona el tipo de agente a utilizar",
                    )
                    with gr.Column():
                        max_steps = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=config['max_steps'],
                            step=1,
                            label="Máximo de Pasos de Ejecución",
                            info="Número máximo de pasos que realizará el agente",
                        )
                        max_actions_per_step = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=config['max_actions_per_step'],
                            step=1,
                            label="Máximo de Acciones por Paso",
                            info="Número máximo de acciones que realizará el agente por paso",
                        )
                    with gr.Column():
                        use_vision = gr.Checkbox(
                            label="Usar Visión",
                            value=config['use_vision'],
                            info="Habilitar capacidades de procesamiento visual",
                        )
                        tool_calling_method = gr.Dropdown(
                            label="Método de Llamada de Herramientas",
                            value=config['tool_calling_method'],
                            interactive=True,
                            allow_custom_value=True,  # Allow users to input custom model names
                            choices=["auto", "json_schema", "function_calling"],
                            info="Nombre de función de llamadas de herramientas",
                            visible=False
                        )

            with gr.TabItem("🔧 Configuración LLM", id=2):
                with gr.Group():
                    llm_provider = gr.Dropdown(
                        choices=[provider for provider,model in utils.model_names.items()],
                        label="Proveedor LLM",
                        value=config['llm_provider'],
                        info="Selecciona tu proveedor de modelo de lenguaje preferido"
                    )
                    llm_model_name = gr.Dropdown(
                        label="Nombre del Modelo",
                        choices=utils.model_names['openai'],
                        value=config['llm_model_name'],
                        interactive=True,
                        allow_custom_value=True,  # Allow users to input custom model names
                        info="Selecciona un modelo del menú o escribe un nombre personalizado"
                    )
                    llm_temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=config['llm_temperature'],
                        step=0.1,
                        label="Temperatura",
                        info="Controla la aleatoriedad en las salidas del modelo"
                    )
                    with gr.Row():
                        llm_base_url = gr.Textbox(
                            label="URL Base",
                            value=config['llm_base_url'],
                            info="URL del endpoint de la API (si es requerida)"
                        )
                        llm_api_key = gr.Textbox(
                            label="Clave API",
                            type="password",
                            value=config['llm_api_key'],
                            info="Tu clave API (deja en blanco para usar .env)"
                        )

            with gr.TabItem("🌐 Configuración del Navegador", id=3):
                with gr.Group():
                    with gr.Row():
                        use_own_browser = gr.Checkbox(
                            label="Usar Navegador Propio",
                            value=config['use_own_browser'],
                            info="Usar tu instancia de navegador existente",
                        )
                        keep_browser_open = gr.Checkbox(
                            label="Mantener Navegador Abierto",
                            value=config['keep_browser_open'],
                            info="Mantener el navegador abierto entre tareas",
                        )
                        # Panel mejorado de modo headless
                        gr.HTML("""
                            <div style="background: linear-gradient(135deg, rgba(128,0,128,0.1), rgba(75,0,130,0.1));
                                        border-radius: 10px; padding: 15px; margin: 10px 0;
                                        border: 1px solid rgba(128,0,128,0.3);">
                                <h4 style="color: #9370db; margin: 0; font-family: 'Exo 2', sans-serif;">
                                    🎭 Control de Modo de Navegador
                                </h4>
                                <p style="color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.9rem;">
                                    Cambia entre modo visible y headless en tiempo real
                                </p>
                            </div>
                        """)

                        with gr.Row():
                            headless = gr.Checkbox(
                                label="Modo Sin Cabeza (Headless)",
                                value=config['headless'],
                                info="Ejecutar navegador sin interfaz gráfica",
                                scale=2
                            )

                            browser_mode_toggle = gr.Button(
                                "🔄 Cambiar Modo",
                                variant="secondary",
                                scale=1
                            )

                        # Estado del navegador
                        browser_status_display = gr.HTML(
                            value=get_enhanced_browser_status_display()
                        )

                        # Estado del programador de tareas
                        scheduler_status_display = gr.HTML(
                            value=get_scheduler_status_display()
                        )
                        disable_security = gr.Checkbox(
                            label="Deshabilitar Seguridad",
                            value=config['disable_security'],
                            info="Deshabilitar características de seguridad del navegador",
                        )
                        enable_recording = gr.Checkbox(
                            label="Habilitar Grabación",
                            value=config['enable_recording'],
                            info="Habilitar guardado de grabaciones del navegador",
                        )

                    with gr.Row():
                        window_w = gr.Number(
                            label="Ancho de Ventana",
                            value=config['window_w'],
                            info="Ancho de la ventana del navegador",
                        )
                        window_h = gr.Number(
                            label="Alto de Ventana",
                            value=config['window_h'],
                            info="Alto de la ventana del navegador",
                        )

                    save_recording_path = gr.Textbox(
                        label="Ruta de Grabaciones",
                        placeholder="ej. ./tmp/record_videos",
                        value=config['save_recording_path'],
                        info="Ruta para guardar grabaciones del navegador",
                        interactive=True,  # Allow editing only if recording is enabled
                    )

                    save_trace_path = gr.Textbox(
                        label="Ruta de Trazas",
                        placeholder="ej. ./tmp/traces",
                        value=config['save_trace_path'],
                        info="Ruta para guardar trazas del agente",
                        interactive=True,
                    )

                    save_agent_history_path = gr.Textbox(
                        label="Ruta de Historial del Agente",
                        placeholder="ej. ./tmp/agent_history",
                        value=config['save_agent_history_path'],
                        info="Especifica el directorio donde se guardará el historial del agente.",
                        interactive=True,
                    )

            with gr.TabItem("🤖 Agente Interactivo", id=4):
                # Header con información del sistema
                gr.HTML("""
                    <div style="background: linear-gradient(135deg, rgba(0,245,255,0.1), rgba(255,0,255,0.1));
                                border-radius: 15px; padding: 20px; margin-bottom: 20px;
                                border: 1px solid rgba(0,245,255,0.3);">
                        <h3 style="color: #00f5ff; margin: 0; font-family: 'Exo 2', sans-serif;">
                            🚀 Sistema Avanzado de Cola de Tareas en Tiempo Real
                        </h3>
                        <p style="color: #e0e0e0; margin: 10px 0 0 0; font-size: 0.9rem;">
                            Envía múltiples tareas, gestiona la cola en tiempo real, programa ejecuciones y controla el progreso sin interrupciones.
                        </p>
                    </div>
                """)

                with gr.Row():
                    # Panel izquierdo: Envío de tareas
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 Nueva Tarea")

                        task_name = gr.Textbox(
                            label="Nombre de la Tarea",
                            placeholder="ej. Buscar noticias en Google",
                            info="Nombre descriptivo para identificar la tarea"
                        )

                        task = gr.Textbox(
                            label="Descripción de la Tarea",
                            lines=4,
                            placeholder="Ingresa tu tarea aquí...\nEjemplo: Ve a Google y busca 'noticias de tecnología'",
                            value=config['task'],
                            info="Describe detalladamente lo que quieres que haga el agente",
                        )

                        add_infos = gr.Textbox(
                            label="Información Adicional",
                            lines=2,
                            placeholder="Contexto adicional, instrucciones específicas...",
                            info="Pistas opcionales para ayudar al LLM",
                        )

                        with gr.Row():
                            task_priority = gr.Number(
                                label="Prioridad",
                                value=1,
                                minimum=1,
                                maximum=10,
                                step=1,
                                scale=1,
                                info="1=Baja, 10=Alta"
                            )

                            execution_mode = gr.Radio(
                                choices=["Inmediato", "Programado", "Diferido"],
                                value="Inmediato",
                                label="Modo de Ejecución",
                                scale=2
                            )

                        # Opciones de programación mejoradas
                        with gr.Group(visible=False) as scheduling_options:
                            gr.HTML("""
                                <div style="background: linear-gradient(135deg, rgba(255,165,0,0.1), rgba(255,215,0,0.1));
                                            border-radius: 10px; padding: 15px; margin-bottom: 15px;
                                            border: 1px solid rgba(255,165,0,0.3);">
                                    <h4 style="color: #ffa500; margin: 0; font-family: 'Exo 2', sans-serif;">
                                        ⏰ Opciones de Programación Avanzada
                                    </h4>
                                    <p style="color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.9rem;">
                                        Configura cuándo quieres que se ejecute tu tarea
                                    </p>
                                </div>
                            """)

                            # Panel para ejecución diferida
                            with gr.Group(visible=False) as delay_options:
                                gr.Markdown("##### 🕐 Ejecución Diferida")

                                with gr.Row():
                                    # Opciones rápidas predefinidas
                                    delay_preset = gr.Radio(
                                        choices=["5 minutos", "15 minutos", "30 minutos", "1 hora", "2 horas", "Personalizado"],
                                        value="5 minutos",
                                        label="Tiempo de Retraso",
                                        scale=2
                                    )

                                    # Campo personalizado para minutos
                                    delay_minutes = gr.Number(
                                        label="Minutos Personalizados",
                                        value=5,
                                        minimum=1,
                                        maximum=1440,
                                        step=1,
                                        scale=1,
                                        visible=False,
                                        info="1-1440 minutos (24 horas máx)"
                                    )

                                # Información de cuándo se ejecutará
                                delay_info = gr.HTML(
                                    value="<div style='color: #00f5ff; font-size: 0.9rem; padding: 10px; background: rgba(0,245,255,0.1); border-radius: 5px; margin-top: 10px;'>📅 Se ejecutará en: <strong>5 minutos</strong></div>"
                                )

                            # Panel para ejecución programada
                            with gr.Group(visible=False) as schedule_options:
                                gr.Markdown("##### 📅 Ejecución Programada")

                                with gr.Row():
                                    # Selector de fecha
                                    import datetime
                                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                                    next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%H")

                                    scheduled_date = gr.Textbox(
                                        label="📅 Fecha",
                                        placeholder=current_date,
                                        value=current_date,
                                        scale=1,
                                        info="Formato: YYYY-MM-DD"
                                    )

                                    # Selector de hora
                                    scheduled_hour = gr.Dropdown(
                                        choices=[f"{i:02d}" for i in range(24)],
                                        label="🕐 Hora",
                                        value=next_hour,
                                        scale=1
                                    )

                                    # Selector de minutos
                                    scheduled_minute = gr.Dropdown(
                                        choices=[f"{i:02d}" for i in range(0, 60, 5)],
                                        label="🕐 Minutos",
                                        value="00",
                                        scale=1
                                    )

                                with gr.Row():
                                    # Botones de tiempo rápido
                                    quick_time_buttons = gr.HTML("""
                                        <div style='display: flex; gap: 10px; margin: 10px 0;'>
                                            <button onclick='setQuickTime("now")' style='background: rgba(0,245,255,0.2); border: 1px solid #00f5ff; color: #00f5ff; padding: 5px 10px; border-radius: 5px; cursor: pointer;'>Ahora</button>
                                            <button onclick='setQuickTime("1h")' style='background: rgba(0,245,255,0.2); border: 1px solid #00f5ff; color: #00f5ff; padding: 5px 10px; border-radius: 5px; cursor: pointer;'>+1 Hora</button>
                                            <button onclick='setQuickTime("tomorrow")' style='background: rgba(0,245,255,0.2); border: 1px solid #00f5ff; color: #00f5ff; padding: 5px 10px; border-radius: 5px; cursor: pointer;'>Mañana 9:00</button>
                                        </div>
                                    """)

                                # Información de cuándo se ejecutará
                                schedule_info = gr.HTML(
                                    value="<div style='color: #00f5ff; font-size: 0.9rem; padding: 10px; background: rgba(0,245,255,0.1); border-radius: 5px; margin-top: 10px;'>📅 Se ejecutará el: <strong>2025-01-15 a las 14:00</strong></div>"
                                )

                        with gr.Row():
                            submit_task_button = gr.Button("➕ Añadir a Cola", variant="primary", scale=2)
                            submit_and_start_button = gr.Button("➕▶️ Añadir y Ejecutar", variant="secondary", scale=2)

                        # Botones de compatibilidad para ejecución directa (modo clásico)
                        gr.Markdown("#### 🎯 Ejecución Directa (Modo Clásico)")
                        with gr.Row():
                            run_button = gr.Button("▶️ Ejecutar Agente Directamente", variant="primary", scale=2)
                            stop_button = gr.Button("⏹️ Detener Ejecución", variant="stop", scale=1)

                    # Panel derecho: Vista del navegador
                    with gr.Column(scale=2):
                        gr.Markdown("### 🌐 Vista del Navegador en Tiempo Real")
                        browser_view = gr.HTML(
                            value="<div style='width:100%; height:50vh; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #00f5ff; font-family: Exo 2; border: 1px solid rgba(0,245,255,0.3);'><h3>🔄 Esperando sesión del navegador...</h3></div>",
                            label="Vista del Navegador en Vivo",
                        )

                # Panel de cola de tareas en tiempo real
                gr.Markdown("### 📋 Cola de Tareas en Tiempo Real")

                with gr.Row():
                    # Controles principales de la cola
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🎮 Controles de Cola")

                        with gr.Row():
                            start_queue_btn = gr.Button("▶️ Iniciar Cola", variant="primary", scale=1)
                            pause_queue_btn = gr.Button("⏸️ Pausar", variant="secondary", scale=1)
                            stop_queue_btn = gr.Button("⏹️ Detener", variant="stop", scale=1)

                        with gr.Row():
                            clear_completed_btn = gr.Button("🗑️ Limpiar Completadas", variant="secondary", scale=1)
                            reset_browser_btn = gr.Button("🔄 Reiniciar Navegador", variant="secondary", scale=1)

                        # Estado general de la cola
                        queue_status = gr.HTML(
                            value="<div style='padding: 15px; background: rgba(0,245,255,0.1); border-radius: 10px; border: 1px solid rgba(0,245,255,0.3);'><h4 style='color: #00f5ff; margin: 0;'>📊 Estado: Cola Vacía</h4><p style='color: #e0e0e0; margin: 5px 0 0 0;'>0 pendientes • 0 ejecutándose • 0 completadas</p></div>"
                        )

                        # Tarea actual en ejecución
                        current_task_display = gr.HTML(
                            value="<div style='padding: 15px; background: rgba(255,165,0,0.1); border-radius: 10px; border: 1px solid rgba(255,165,0,0.3); margin-top: 10px;'><h4 style='color: #ffa500; margin: 0;'>🔄 Tarea Actual</h4><p style='color: #e0e0e0; margin: 5px 0 0 0;'>Ninguna tarea en ejecución</p></div>"
                        )

                    # Lista detallada de tareas
                    with gr.Column(scale=2):
                        gr.Markdown("#### 📝 Lista de Tareas")

                        # Filtros y búsqueda
                        with gr.Row():
                            task_filter = gr.Radio(
                                choices=["Todas", "Pendientes", "Ejecutándose", "Completadas", "Fallidas"],
                                value="Todas",
                                label="Filtrar por Estado",
                                scale=2
                            )

                            search_tasks = gr.Textbox(
                                placeholder="Buscar tareas...",
                                label="Buscar",
                                scale=1
                            )

                        # Lista de tareas con controles individuales
                        tasks_list = gr.HTML(
                            value="""
                            <div style='background: rgba(26,26,46,0.6); border-radius: 10px; padding: 20px; border: 1px solid rgba(0,245,255,0.2); min-height: 300px;'>
                                <div style='text-align: center; color: #888; padding: 50px;'>
                                    <h3>📋 No hay tareas en la cola</h3>
                                    <p>Añade una nueva tarea para comenzar</p>
                                </div>
                            </div>
                            """,
                            label="Tareas"
                        )

                # Panel de gestión individual de tareas
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🎯 Gestión Individual de Tareas")

                        selected_task_id = gr.Textbox(
                            label="ID de Tarea Seleccionada",
                            placeholder="Selecciona una tarea de la lista...",
                            interactive=True
                        )

                        with gr.Row():
                            pause_task_btn = gr.Button("⏸️ Pausar Tarea", variant="secondary", scale=1)
                            resume_task_btn = gr.Button("▶️ Reanudar", variant="primary", scale=1)
                            stop_task_btn = gr.Button("⏹️ Detener", variant="stop", scale=1)

                        with gr.Row():
                            move_up_task_btn = gr.Button("⬆️ Subir Prioridad", variant="secondary", scale=1)
                            move_down_task_btn = gr.Button("⬇️ Bajar Prioridad", variant="secondary", scale=1)
                            delete_task_btn = gr.Button("🗑️ Eliminar", variant="stop", scale=1)

                    with gr.Column(scale=2):
                        gr.Markdown("#### 📊 Estadísticas y Progreso")

                        # Estadísticas en tiempo real
                        stats_display = gr.HTML(
                            value="""
                            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px;'>
                                <div style='background: rgba(0,245,255,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(0,245,255,0.3);'>
                                    <h4 style='color: #00f5ff; margin: 0; font-size: 1.2rem;'>0</h4>
                                    <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Pendientes</p>
                                </div>
                                <div style='background: rgba(255,165,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(255,165,0,0.3);'>
                                    <h4 style='color: #ffa500; margin: 0; font-size: 1.2rem;'>0</h4>
                                    <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Ejecutándose</p>
                                </div>
                                <div style='background: rgba(0,255,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(0,255,0,0.3);'>
                                    <h4 style='color: #00ff00; margin: 0; font-size: 1.2rem;'>0</h4>
                                    <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Completadas</p>
                                </div>
                                <div style='background: rgba(255,0,0,0.1); border-radius: 8px; padding: 15px; text-align: center; border: 1px solid rgba(255,0,0,0.3);'>
                                    <h4 style='color: #ff0000; margin: 0; font-size: 1.2rem;'>0</h4>
                                    <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.8rem;'>Fallidas</p>
                                </div>
                            </div>
                            """
                        )

                        # Progreso de la tarea actual
                        task_progress = gr.HTML(
                            value="""
                            <div style='background: rgba(26,26,46,0.6); border-radius: 10px; padding: 20px; border: 1px solid rgba(0,245,255,0.2);'>
                                <h4 style='color: #00f5ff; margin: 0 0 10px 0;'>📈 Progreso de Tarea Actual</h4>
                                <div style='background: rgba(0,0,0,0.3); border-radius: 5px; height: 20px; overflow: hidden; margin-bottom: 10px;'>
                                    <div style='background: linear-gradient(90deg, #00f5ff, #0080ff); height: 100%; width: 0%; transition: width 0.3s ease;'></div>
                                </div>
                                <p style='color: #e0e0e0; margin: 0; font-size: 0.9rem;'>Esperando tarea...</p>
                            </div>
                            """
                        )

                # ============================================================================
                # MANEJADORES DE EVENTOS PARA COLA AVANZADA DE TAREAS
                # ============================================================================

                # Actualizar visibilidad de opciones de programación
                execution_mode.change(
                    fn=update_scheduling_visibility,
                    inputs=execution_mode,
                    outputs=[scheduling_options, delay_options, schedule_options]
                )

                # Actualizar campo de minutos según preset seleccionado
                delay_preset.change(
                    fn=update_delay_preset,
                    inputs=delay_preset,
                    outputs=[delay_minutes, delay_info]
                )

                # Actualizar información de programación cuando cambian fecha/hora
                scheduled_date.change(
                    fn=update_schedule_info,
                    inputs=[scheduled_date, scheduled_hour, scheduled_minute],
                    outputs=schedule_info
                )

                scheduled_hour.change(
                    fn=update_schedule_info,
                    inputs=[scheduled_date, scheduled_hour, scheduled_minute],
                    outputs=schedule_info
                )

                scheduled_minute.change(
                    fn=update_schedule_info,
                    inputs=[scheduled_date, scheduled_hour, scheduled_minute],
                    outputs=schedule_info
                )

                # Botón para añadir tarea a la cola
                submit_task_button.click(
                    fn=add_advanced_task_to_queue,
                    inputs=[task_name, task, add_infos, task_priority, execution_mode, delay_preset, delay_minutes, scheduled_date, scheduled_hour, scheduled_minute],
                    outputs=[tasks_list]
                )

                # Botón para añadir tarea y ejecutar inmediatamente
                submit_and_start_button.click(
                    fn=add_and_start_advanced_task,
                    inputs=[task_name, task, add_infos, task_priority, execution_mode, delay_preset, delay_minutes, scheduled_date, scheduled_hour, scheduled_minute],
                    outputs=[tasks_list]
                )

                # Controles principales de la cola
                start_queue_btn.click(
                    fn=start_queue_processing_sync,
                    outputs=[queue_status, tasks_list]
                )

                pause_queue_btn.click(
                    fn=pause_queue_sync,
                    outputs=[queue_status, tasks_list]
                )

                stop_queue_btn.click(
                    fn=stop_queue_processing_sync,
                    outputs=[queue_status, tasks_list]
                )

                clear_completed_btn.click(
                    fn=clear_completed_tasks_sync,
                    outputs=[queue_status, tasks_list]
                )

                reset_browser_btn.click(
                    fn=reset_browser_session_sync,
                    outputs=[queue_status, tasks_list]
                )

                # Controles individuales de tareas
                pause_task_btn.click(
                    fn=pause_individual_task,
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                resume_task_btn.click(
                    fn=resume_individual_task,
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                stop_task_btn.click(
                    fn=stop_individual_task,
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                move_up_task_btn.click(
                    fn=lambda task_id: reorder_task_in_queue_sync(task_id, "up"),
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                move_down_task_btn.click(
                    fn=lambda task_id: reorder_task_in_queue_sync(task_id, "down"),
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                delete_task_btn.click(
                    fn=remove_task_from_queue_sync,
                    inputs=selected_task_id,
                    outputs=[tasks_list]
                )

                # Actualización automática en tiempo real
                def refresh_advanced_queue():
                    return get_advanced_queue_display(), get_queue_stats_display(), get_current_task_display()

                # Evento para cambio de modo del navegador (manual)
                browser_mode_toggle.click(
                    fn=toggle_browser_mode,
                    outputs=[browser_status_display]
                )

                # Evento automático para cambio de modo basado en configuración
                headless.change(
                    fn=auto_switch_headless_mode,
                    inputs=headless,
                    outputs=[browser_status_display]
                )

                # Timer para actualización automática cada 2 segundos
                advanced_queue_timer = gr.Timer(value=2)
                advanced_queue_timer.tick(
                    fn=refresh_advanced_queue,
                    outputs=[tasks_list, stats_display, current_task_display]
                )

                # Timer para actualización de estados del sistema cada 5 segundos
                system_status_timer = gr.Timer(value=5)
                system_status_timer.tick(
                    fn=lambda: (get_enhanced_browser_status_display(), get_scheduler_status_display()),
                    outputs=[browser_status_display, scheduler_status_display]
                )

            with gr.TabItem("📁 Configuración", id=7):
                with gr.Group():
                    config_file_input = gr.File(
                        label="Cargar Archivo de Configuración",
                        file_types=[".pkl"],
                        interactive=True
                    )

                    load_config_button = gr.Button("Cargar Configuración Existente desde Archivo", variant="primary")
                    save_config_button = gr.Button("Guardar Configuración Actual", variant="primary")

                    config_status = gr.Textbox(
                        label="Estado",
                        lines=2,
                        interactive=False
                    )

                load_config_button.click(
                    fn=update_ui_from_config,
                    inputs=[config_file_input],
                    outputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security, enable_recording,
                        window_w, window_h, save_recording_path, save_trace_path, save_agent_history_path,
                        task, config_status
                    ]
                )

                save_config_button.click(
                    fn=save_current_config,
                    inputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security,
                        enable_recording, window_w, window_h, save_recording_path, save_trace_path,
                        save_agent_history_path, task,
                    ],  
                    outputs=[config_status]
                )

            with gr.TabItem("📋 Cola de Tareas", id=5):
                with gr.Group():
                    gr.Markdown("### Gestión de Cola de Tareas")

                    # Add new task section
                    with gr.Group():
                        gr.Markdown("#### Añadir Nueva Tarea")
                        with gr.Row():
                            new_task_name = gr.Textbox(
                                label="Nombre de la Tarea",
                                placeholder="ej. Buscar OpenAI",
                                scale=2
                            )
                            new_task_priority = gr.Number(
                                label="Prioridad",
                                value=0,
                                precision=0,
                                scale=1,
                                info="Números más altos = mayor prioridad"
                            )

                        new_task_description = gr.Textbox(
                            label="Descripción de la Tarea",
                            lines=3,
                            placeholder="Describe lo que quieres que haga el agente...",
                        )

                        new_task_additional_info = gr.Textbox(
                            label="Información Adicional",
                            lines=2,
                            placeholder="Contexto o instrucciones opcionales...",
                        )

                        with gr.Row():
                            add_task_button = gr.Button("➕ Añadir a la Cola", variant="primary", scale=2)
                            add_and_start_button = gr.Button("➕▶️ Añadir e Iniciar Cola", variant="secondary", scale=2)

                    # Queue control section
                    with gr.Group():
                        gr.Markdown("#### Controles de Cola")
                        with gr.Row():
                            start_queue_button = gr.Button("▶️ Iniciar Cola", variant="primary")
                            pause_queue_button = gr.Button("⏸️ Pausar Cola", variant="secondary")
                            resume_queue_button = gr.Button("⏯️ Reanudar Cola", variant="secondary")
                            stop_queue_button = gr.Button("⏹️ Detener Cola", variant="stop")

                        with gr.Row():
                            clear_completed_button = gr.Button("🗑️ Limpiar Completadas", variant="secondary")
                            reset_browser_button = gr.Button("🔄 Reiniciar Navegador", variant="secondary")
                            update_config_button = gr.Button("🔧 Actualizar Configuración", variant="secondary")

                    # Queue display
                    queue_display = gr.Textbox(
                        label="Estado de la Cola",
                        lines=15,
                        value=get_queue_display(),
                        interactive=False,
                        show_label=True
                    )

                    # Task management section
                    with gr.Group():
                        gr.Markdown("#### Gestión de Tareas")
                        with gr.Row():
                            task_id_input = gr.Textbox(
                                label="ID de Tarea",
                                placeholder="Ingresa el ID de tarea para operaciones...",
                                scale=2
                            )
                            with gr.Column(scale=1):
                                move_up_button = gr.Button("⬆️ Subir")
                                move_down_button = gr.Button("⬇️ Bajar")
                                remove_task_button = gr.Button("🗑️ Eliminar", variant="stop")

                    # Status message
                    queue_status_message = gr.Textbox(
                        label="Estado",
                        lines=2,
                        interactive=False
                    )

                    # Auto-refresh queue display every 3 seconds
                    def refresh_queue_display():
                        return get_queue_display()

                    # Set up periodic refresh
                    queue_refresh_timer = gr.Timer(value=3)
                    queue_refresh_timer.tick(
                        fn=refresh_queue_display,
                        outputs=queue_display
                    )

                    # Button event handlers
                    add_task_button.click(
                        fn=add_task_to_queue_sync,
                        inputs=[new_task_name, new_task_description, new_task_additional_info, new_task_priority],
                        outputs=[queue_status_message, queue_display]
                    )

                    add_and_start_button.click(
                        fn=add_and_start_queue_handler_sync,
                        inputs=[new_task_name, new_task_description, new_task_additional_info, new_task_priority],
                        outputs=[queue_status_message, queue_display]
                    )

                    start_queue_button.click(
                        fn=start_queue_processing_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    pause_queue_button.click(
                        fn=pause_queue_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    resume_queue_button.click(
                        fn=resume_queue_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    stop_queue_button.click(
                        fn=stop_queue_processing_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    clear_completed_button.click(
                        fn=clear_completed_tasks_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    reset_browser_button.click(
                        fn=reset_browser_session_sync,
                        outputs=[queue_status_message, queue_display]
                    )

                    update_config_button.click(
                        fn=force_update_task_processor_config,
                        inputs=[
                            llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                            agent_type, use_own_browser, headless, disable_security, window_w, window_h,
                            save_recording_path, save_agent_history_path, save_trace_path, enable_recording,
                            max_steps, use_vision, max_actions_per_step, tool_calling_method
                        ],
                        outputs=[queue_status_message, queue_display]
                    )

                    move_up_button.click(
                        fn=lambda task_id: reorder_task_in_queue_sync(task_id, "up"),
                        inputs=task_id_input,
                        outputs=[queue_status_message, queue_display]
                    )

                    move_down_button.click(
                        fn=lambda task_id: reorder_task_in_queue_sync(task_id, "down"),
                        inputs=task_id_input,
                        outputs=[queue_status_message, queue_display]
                    )

                    remove_task_button.click(
                        fn=remove_task_from_queue_sync,
                        inputs=task_id_input,
                        outputs=[queue_status_message, queue_display]
                    )

            with gr.TabItem("📊 Resultados", id=8):
                with gr.Group():

                    recording_display = gr.Video(label="Última Grabación")

                    gr.Markdown("### Resultados")
                    with gr.Row():
                        with gr.Column():
                            final_result_output = gr.Textbox(
                                label="Resultado Final", lines=3, show_label=True
                            )
                        with gr.Column():
                            errors_output = gr.Textbox(
                                label="Errores", lines=3, show_label=True
                            )
                    with gr.Row():
                        with gr.Column():
                            model_actions_output = gr.Textbox(
                                label="Acciones del Modelo", lines=3, show_label=True
                            )
                        with gr.Column():
                            model_thoughts_output = gr.Textbox(
                                label="Pensamientos del Modelo", lines=3, show_label=True
                            )

                    trace_file = gr.File(label="Archivo de Traza")

                    agent_history_file = gr.File(label="Historial del Agente")

                # Bind the stop button click event after errors_output is defined
                stop_button.click(
                    fn=stop_agent,
                    inputs=[],
                    outputs=[errors_output, stop_button, run_button],
                )

                # Run button click handler
                run_button.click(
                    fn=run_with_stream,
                        inputs=[
                            agent_type, llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                            use_own_browser, keep_browser_open, headless, disable_security, window_w, window_h,
                            save_recording_path, save_agent_history_path, save_trace_path,  # Include the new path
                            enable_recording, task, add_infos, max_steps, use_vision, max_actions_per_step, tool_calling_method
                        ],
                    outputs=[
                        browser_view,           # Browser view
                        final_result_output,    # Final result
                        errors_output,          # Errors
                        model_actions_output,   # Model actions
                        model_thoughts_output,  # Model thoughts
                        recording_display,      # Latest recording
                        trace_file,             # Trace file
                        agent_history_file,     # Agent history file
                        stop_button,            # Stop button
                        run_button              # Run button
                    ],
                )

            with gr.TabItem("🎥 Grabaciones", id=9):
                def list_recordings(save_recording_path):
                    if not os.path.exists(save_recording_path):
                        return []

                    # Get all video files
                    recordings = glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4")) + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))

                    # Sort recordings by creation time (oldest first)
                    recordings.sort(key=os.path.getctime)

                    # Add numbering to the recordings
                    numbered_recordings = []
                    for idx, recording in enumerate(recordings, start=1):
                        filename = os.path.basename(recording)
                        numbered_recordings.append((recording, f"{idx}. {filename}"))

                    return numbered_recordings

                recordings_gallery = gr.Gallery(
                    label="Grabaciones",
                    value=list_recordings(config['save_recording_path']),
                    columns=3,
                    height="auto",
                    object_fit="contain"
                )

                refresh_button = gr.Button("🔄 Actualizar Grabaciones", variant="secondary")
                refresh_button.click(
                    fn=list_recordings,
                    inputs=save_recording_path,
                    outputs=recordings_gallery
                )

        # Attach the callback to the LLM provider dropdown
        llm_provider.change(
            lambda provider, api_key, base_url: update_model_dropdown(provider, api_key, base_url),
            inputs=[llm_provider, llm_api_key, llm_base_url],
            outputs=llm_model_name
        )

        # Add this after defining the components
        enable_recording.change(
            lambda enabled: gr.update(interactive=enabled),
            inputs=enable_recording,
            outputs=save_recording_path
        )

        use_own_browser.change(fn=close_global_browser)
        keep_browser_open.change(fn=close_global_browser)

        # Configure task processor with current settings
        def update_task_processor_config():
            config = {
                'agent_type': agent_type.value,
                'llm_provider': llm_provider.value,
                'llm_model_name': llm_model_name.value,
                'llm_temperature': llm_temperature.value,
                'llm_base_url': llm_base_url.value,
                'llm_api_key': llm_api_key.value,
                'use_own_browser': use_own_browser.value,
                'headless': headless.value,
                'disable_security': disable_security.value,
                'window_w': int(window_w.value),
                'window_h': int(window_h.value),
                'save_recording_path': save_recording_path.value,
                'save_agent_history_path': save_agent_history_path.value,
                'save_trace_path': save_trace_path.value,
                'enable_recording': enable_recording.value,
                'max_steps': int(max_steps.value),
                'use_vision': use_vision.value,
                'max_actions_per_step': int(max_actions_per_step.value),
                'tool_calling_method': tool_calling_method.value
            }
            task_processor.set_config(config)

        # Update task processor config when settings change
        for component in [agent_type, llm_provider, llm_model_name, llm_temperature,
                         llm_base_url, llm_api_key, use_own_browser, headless,
                         disable_security, window_w, window_h, save_recording_path,
                         save_agent_history_path, save_trace_path, enable_recording,
                         max_steps, use_vision, max_actions_per_step, tool_calling_method]:
            component.change(fn=update_task_processor_config)

        # Add footer
        gr.HTML(
            """
            <div class="footer-text">
                <strong>BOTIDINAMIX AI</strong> - Todos los derechos reservados 2025
            </div>
            """,
        )

        # Initialize browser and scheduler system on startup
        demo.load(fn=initialize_browser_and_scheduler)

        # Auto-initialize browser with current configuration on startup
        demo.load(
            fn=auto_initialize_browser_on_startup,
            inputs=[headless, disable_security, window_w, window_h],
            outputs=browser_status_display
        )

    return demo

def main():
    parser = argparse.ArgumentParser(description="Interfaz Gradio para Agente de Navegador")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Dirección IP a la que enlazar")
    parser.add_argument("--port", type=int, default=7788, help="Puerto en el que escuchar")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Tema a usar para la interfaz")
    parser.add_argument("--dark-mode", action="store_true", help="Habilitar modo oscuro")
    parser.add_argument("--auto-open", action="store_true", help="Abrir navegador automáticamente")
    args = parser.parse_args()

    config_dict = default_config()

    demo = create_ui(config_dict, theme_name=args.theme)

    # Configuración mejorada para evitar problemas de conexión
    try:
        print(f"🚀 Iniciando AUTONOBOT en http://{args.ip}:{args.port}")
        print("📱 Interfaz futurista con modelos Gemini actualizados")
        print("🛑 Presiona Ctrl+C para detener el servidor")

        demo.launch(
            server_name=args.ip,
            server_port=args.port,
            share=False,
            inbrowser=args.auto_open,
            prevent_thread_lock=False,
            show_error=True,
            quiet=False,
            favicon_path=None,
            ssl_keyfile=None,
            ssl_certfile=None,
            ssl_keyfile_password=None
        )
    except Exception as e:
        print(f"❌ Error al lanzar AUTONOBOT: {e}")
        print("🔧 Intentando con puerto alternativo...")

        # Intentar con puerto alternativo
        try:
            demo.launch(
                server_name=args.ip,
                server_port=args.port + 1,
                share=False,
                inbrowser=args.auto_open,
                prevent_thread_lock=False,
                show_error=True,
                quiet=False
            )
            print(f"✅ AUTONOBOT iniciado en puerto alternativo: {args.port + 1}")
        except Exception as e2:
            print(f"💥 Error crítico: {e2}")
            print("🔧 Soluciones sugeridas:")
            print("   1. Reiniciar el sistema")
            print("   2. Verificar firewall/antivirus")
            print("   3. Usar: python fix_gradio_connection.py")

if __name__ == '__main__':
    main()
