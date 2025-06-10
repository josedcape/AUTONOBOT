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
        return f"Task '{task_name}' added to queue (ID: {task_id})", get_queue_display()
    except Exception as e:
        return f"Error adding task: {str(e)}", get_queue_display()

async def remove_task_from_queue(task_id):
    """Remove a task from the queue"""
    try:
        success = await task_queue.remove_task(task_id)
        if success:
            return "Task removed from queue", get_queue_display()
        else:
            return "Task not found or cannot be removed", get_queue_display()
    except Exception as e:
        return f"Error removing task: {str(e)}", get_queue_display()

async def update_task_in_queue(task_id, task_name, task_description, additional_info="", priority=0):
    """Update a task in the queue"""
    try:
        success = await task_queue.update_task(task_id, task_name, task_description, additional_info, priority)
        if success:
            return "Task updated", get_queue_display()
        else:
            return "Task not found or cannot be updated", get_queue_display()
    except Exception as e:
        return f"Error updating task: {str(e)}", get_queue_display()

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
            return "Task not found", get_queue_display()

        if direction == "up" and current_pos > 0:
            new_pos = current_pos - 1
        elif direction == "down" and current_pos < len(tasks) - 1:
            new_pos = current_pos + 1
        else:
            return "Cannot move task in that direction", get_queue_display()

        success = await task_queue.reorder_task(task_id, new_pos)
        if success:
            return f"Task moved {direction}", get_queue_display()
        else:
            return "Failed to reorder task", get_queue_display()
    except Exception as e:
        return f"Error reordering task: {str(e)}", get_queue_display()

def get_queue_display():
    """Get formatted queue display"""
    status = task_queue.get_queue_status()
    tasks = task_queue.get_all_tasks()

    if not tasks:
        return "Queue is empty"

    display_lines = [
        f"📊 Queue Status: {status['pending']} pending, {status['running']} running, {status['completed']} completed, {status['failed']} failed",
        f"⏸️ Paused: {'Yes' if status['is_paused'] else 'No'}",
        ""
    ]

    for i, task in enumerate(tasks, 1):
        status_emoji = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'paused': '⏸️',
            'cancelled': '🚫'
        }.get(task['status'], '❓')

        display_lines.append(f"{i}. {status_emoji} {task['name']} ({task['status']})")
        if task['status'] == 'running':
            display_lines.append(f"   📝 {task['description'][:100]}...")
        elif task['status'] in ['completed', 'failed'] and task.get('result'):
            display_lines.append(f"   📝 {task['result'][:100]}...")

    return "\n".join(display_lines)

async def start_queue_processing():
    """Start processing the task queue"""
    try:
        if task_processor.is_processing():
            return "Queue is already processing", get_queue_display()

        # Set up the task processor with the agent runner
        task_processor.set_agent_runner(run_browser_agent)

        # Ensure task processor has current configuration
        # This is critical - without this, it uses default OpenAI config
        logger.info("🔧 Updating task processor configuration...")
        current_config = task_processor._config
        if not current_config or not current_config.get('llm_api_key'):
            logger.warning("⚠️ Task processor has no LLM configuration! Using defaults may cause Connection errors.")
            logger.info(f"Current config: {current_config}")
        else:
            logger.info(f"✅ Task processor configured with LLM: {current_config.get('llm_provider', 'unknown')}")

        # Start processing in background using threading to avoid asyncio conflicts
        import threading
        def start_processor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(task_processor.start_processing())
            except Exception as e:
                logger.error(f"Task processor thread error: {e}")
            finally:
                loop.close()

        processor_thread = threading.Thread(target=start_processor, daemon=True)
        processor_thread.start()

        return "Queue processing started", get_queue_display()
    except Exception as e:
        return f"Error starting queue: {str(e)}", get_queue_display()

async def stop_queue_processing():
    """Stop processing the task queue"""
    try:
        await task_processor.stop_processing()
        return "Queue processing stopped", get_queue_display()
    except Exception as e:
        return f"Error stopping queue: {str(e)}", get_queue_display()

async def pause_queue():
    """Pause the task queue"""
    try:
        await task_queue.pause_queue()
        return "Queue paused", get_queue_display()
    except Exception as e:
        return f"Error pausing queue: {str(e)}", get_queue_display()

async def resume_queue():
    """Resume the task queue"""
    try:
        await task_queue.resume_queue()
        return "Queue resumed", get_queue_display()
    except Exception as e:
        return f"Error resuming queue: {str(e)}", get_queue_display()

async def clear_completed_tasks():
    """Clear completed and failed tasks"""
    try:
        await task_queue.clear_completed_tasks()
        return "Completed tasks cleared", get_queue_display()
    except Exception as e:
        return f"Error clearing tasks: {str(e)}", get_queue_display()

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
        return f"Error adding task: {str(e)}", get_queue_display()

def remove_task_from_queue_sync(task_id):
    """Synchronous wrapper for remove_task_from_queue"""
    try:
        return run_async_in_thread(remove_task_from_queue(task_id))
    except Exception as e:
        return f"Error removing task: {str(e)}", get_queue_display()

def reorder_task_in_queue_sync(task_id, direction):
    """Synchronous wrapper for reorder_task_in_queue"""
    try:
        return run_async_in_thread(reorder_task_in_queue(task_id, direction))
    except Exception as e:
        return f"Error reordering task: {str(e)}", get_queue_display()

def start_queue_processing_sync():
    """Synchronous wrapper for start_queue_processing"""
    try:
        return run_async_in_thread(start_queue_processing())
    except Exception as e:
        return f"Error starting queue: {str(e)}", get_queue_display()

def stop_queue_processing_sync():
    """Synchronous wrapper for stop_queue_processing"""
    try:
        return run_async_in_thread(stop_queue_processing())
    except Exception as e:
        return f"Error stopping queue: {str(e)}", get_queue_display()

def pause_queue_sync():
    """Synchronous wrapper for pause_queue"""
    try:
        return run_async_in_thread(pause_queue())
    except Exception as e:
        return f"Error pausing queue: {str(e)}", get_queue_display()

def resume_queue_sync():
    """Synchronous wrapper for resume_queue"""
    try:
        return run_async_in_thread(resume_queue())
    except Exception as e:
        return f"Error resuming queue: {str(e)}", get_queue_display()

def clear_completed_tasks_sync():
    """Synchronous wrapper for clear_completed_tasks"""
    try:
        return run_async_in_thread(clear_completed_tasks())
    except Exception as e:
        return f"Error clearing tasks: {str(e)}", get_queue_display()

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

        return "Browser session reset successfully", get_queue_display()
    except Exception as e:
        return f"Error resetting browser: {str(e)}", get_queue_display()

def reset_browser_session_sync():
    """Synchronous wrapper for reset_browser_session"""
    try:
        return run_async_in_thread(reset_browser_session())
    except Exception as e:
        return f"Error resetting browser: {str(e)}", get_queue_display()

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

        return f"✅ Task processor configured with {llm_provider} ({llm_model_name})", get_queue_display()
    except Exception as e:
        logger.error(f"Failed to update task processor config: {e}")
        return f"❌ Error updating config: {str(e)}", get_queue_display()

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
        message = "Stop requested - the agent will halt at the next safe point"
        logger.info(f"🛑 {message}")

        # Return UI updates
        return (
            message,                                        # errors_output
            gr.update(value="Stopping...", interactive=False),  # stop_button
            gr.update(interactive=False),                      # run_button
        )
    except Exception as e:
        error_msg = f"Error during stop: {str(e)}"
        logger.error(error_msg)
        return (
            error_msg,
            gr.update(value="Stop", interactive=True),
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
        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
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
            html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
            final_result = errors = model_actions = model_thoughts = ""
            latest_videos = trace = history_file = None


            # Periodically update the stream while the agent task is running
            while not agent_task.done():
                try:
                    encoded_screenshot = await capture_screenshot(_global_browser_context)
                    if encoded_screenshot is not None:
                        html_content = f'<img src="data:image/jpeg;base64,{encoded_screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"
                except Exception as e:
                    html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"

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
                        gr.update(value="Stopping...", interactive=False),  # stop_button
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
                        gr.update(value="Stop", interactive=True),  # Re-enable stop button
                        gr.update(interactive=True)  # Re-enable run button
                    ]
                await asyncio.sleep(0.05)

            # Once the agent task completes, get the results
            try:
                result = await agent_task
                final_result, errors, model_actions, model_thoughts, latest_videos, trace, history_file, stop_button, run_button = result
            except Exception as e:
                errors = f"Agent error: {str(e)}"

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
                f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>",
                "",
                f"Error: {str(e)}\n{traceback.format_exc()}",
                "",
                "",
                None,
                None,
                None,
                gr.update(value="Stop", interactive=True),  # Re-enable stop button
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

    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
        padding-top: 20px !important;
        padding-bottom: 80px !important;
        background: radial-gradient(circle at top, #1b1b1b, #000000 80%);
        color: #e8e8e8;
        overflow-x: hidden;
    }

    .gradio-container::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        background: repeating-linear-gradient(
            135deg,
            rgba(255, 0, 255, 0.15) 0px,
            rgba(255, 0, 255, 0.15) 2px,
            transparent 2px,
            transparent 4px
        );
        animation: gridMove 20s linear infinite;
        z-index: -1;
    }

    @keyframes gridMove {
        from { transform: translate(0, 0); }
        to { transform: translate(100px, 100px); }
    }

    .header-text {
        text-align: center;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #540d6e 0%, #ee0979 50%, #00e0ff 100%);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 0 20px rgba(238,9,121,0.6);
        position: relative;
        overflow: hidden;
        color: #ffffff;
    }

    .header-text::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%);
        animation: shine 3s linear infinite;
    }

    @keyframes shine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .autonobot-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff00, #ffff00);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease-in-out infinite;
        text-shadow: 0 0 30px rgba(0,245,255,0.5);
        margin-bottom: 10px !important;
        letter-spacing: 3px;
    }

    .autonobot-subtitle {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 1.3rem !important;
        font-weight: 300 !important;
        color: #f2f2f2 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 10px !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
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

    .theme-section {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 10px;
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
    """

    with gr.Blocks(
            title="AUTONOBOT - Agente de Navegación Autónoma", theme=theme_map[theme_name], css=css, js=js
    ) as demo:
        with gr.Row():
            gr.HTML(
                """
                <div class="header-text">
                    <h1 class="autonobot-title">🤖 AUTONOBOT</h1>
                    <h3 class="autonobot-subtitle">Agente de Navegación Autónoma</h3>
                </div>
                """,
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("⚙️ Agent Settings", id=1):
                with gr.Group():
                    agent_type = gr.Radio(
                        ["org", "custom"],
                        label="Agent Type",
                        value=config['agent_type'],
                        info="Select the type of agent to use",
                    )
                    with gr.Column():
                        max_steps = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=config['max_steps'],
                            step=1,
                            label="Max Run Steps",
                            info="Maximum number of steps the agent will take",
                        )
                        max_actions_per_step = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=config['max_actions_per_step'],
                            step=1,
                            label="Max Actions per Step",
                            info="Maximum number of actions the agent will take per step",
                        )
                    with gr.Column():
                        use_vision = gr.Checkbox(
                            label="Use Vision",
                            value=config['use_vision'],
                            info="Enable visual processing capabilities",
                        )
                        tool_calling_method = gr.Dropdown(
                            label="Tool Calling Method",
                            value=config['tool_calling_method'],
                            interactive=True,
                            allow_custom_value=True,  # Allow users to input custom model names
                            choices=["auto", "json_schema", "function_calling"],
                            info="Tool Calls Funtion Name",
                            visible=False
                        )

            with gr.TabItem("🔧 LLM Configuration", id=2):
                with gr.Group():
                    llm_provider = gr.Dropdown(
                        choices=[provider for provider,model in utils.model_names.items()],
                        label="LLM Provider",
                        value=config['llm_provider'],
                        info="Select your preferred language model provider"
                    )
                    llm_model_name = gr.Dropdown(
                        label="Model Name",
                        choices=utils.model_names['openai'],
                        value=config['llm_model_name'],
                        interactive=True,
                        allow_custom_value=True,  # Allow users to input custom model names
                        info="Select a model from the dropdown or type a custom model name"
                    )
                    llm_temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=config['llm_temperature'],
                        step=0.1,
                        label="Temperature",
                        info="Controls randomness in model outputs"
                    )
                    with gr.Row():
                        llm_base_url = gr.Textbox(
                            label="Base URL",
                            value=config['llm_base_url'],
                            info="API endpoint URL (if required)"
                        )
                        llm_api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                            value=config['llm_api_key'],
                            info="Your API key (leave blank to use .env)"
                        )

            with gr.TabItem("🌐 Browser Settings", id=3):
                with gr.Group():
                    with gr.Row():
                        use_own_browser = gr.Checkbox(
                            label="Use Own Browser",
                            value=config['use_own_browser'],
                            info="Use your existing browser instance",
                        )
                        keep_browser_open = gr.Checkbox(
                            label="Keep Browser Open",
                            value=config['keep_browser_open'],
                            info="Keep Browser Open between Tasks",
                        )
                        headless = gr.Checkbox(
                            label="Headless Mode",
                            value=config['headless'],
                            info="Run browser without GUI",
                        )
                        disable_security = gr.Checkbox(
                            label="Disable Security",
                            value=config['disable_security'],
                            info="Disable browser security features",
                        )
                        enable_recording = gr.Checkbox(
                            label="Enable Recording",
                            value=config['enable_recording'],
                            info="Enable saving browser recordings",
                        )

                    with gr.Row():
                        window_w = gr.Number(
                            label="Window Width",
                            value=config['window_w'],
                            info="Browser window width",
                        )
                        window_h = gr.Number(
                            label="Window Height",
                            value=config['window_h'],
                            info="Browser window height",
                        )

                    save_recording_path = gr.Textbox(
                        label="Recording Path",
                        placeholder="e.g. ./tmp/record_videos",
                        value=config['save_recording_path'],
                        info="Path to save browser recordings",
                        interactive=True,  # Allow editing only if recording is enabled
                    )

                    save_trace_path = gr.Textbox(
                        label="Trace Path",
                        placeholder="e.g. ./tmp/traces",
                        value=config['save_trace_path'],
                        info="Path to save Agent traces",
                        interactive=True,
                    )

                    save_agent_history_path = gr.Textbox(
                        label="Agent History Save Path",
                        placeholder="e.g., ./tmp/agent_history",
                        value=config['save_agent_history_path'],
                        info="Specify the directory where agent history should be saved.",
                        interactive=True,
                    )

            with gr.TabItem("🤖 Run Agent", id=4):
                task = gr.Textbox(
                    label="Task Description",
                    lines=4,
                    placeholder="Enter your task here...",
                    value=config['task'],
                    info="Describe what you want the agent to do",
                )
                add_infos = gr.Textbox(
                    label="Additional Information",
                    lines=3,
                    placeholder="Add any helpful context or instructions...",
                    info="Optional hints to help the LLM complete the task",
                )

                with gr.Row():
                    run_button = gr.Button("▶️ Run Agent", variant="primary", scale=2)
                    stop_button = gr.Button("⏹️ Stop", variant="stop", scale=1)
                    
                with gr.Row():
                    browser_view = gr.HTML(
                        value="<h1 style='width:80vw; height:50vh'>Waiting for browser session...</h1>",
                        label="Live Browser View",
                )

            with gr.TabItem("📁 Configuration", id=7):
                with gr.Group():
                    config_file_input = gr.File(
                        label="Load Config File",
                        file_types=[".pkl"],
                        interactive=True
                    )

                    load_config_button = gr.Button("Load Existing Config From File", variant="primary")
                    save_config_button = gr.Button("Save Current Config", variant="primary")

                    config_status = gr.Textbox(
                        label="Status",
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

            with gr.TabItem("📋 Task Queue", id=5):
                with gr.Group():
                    gr.Markdown("### Task Queue Management")

                    # Add new task section
                    with gr.Group():
                        gr.Markdown("#### Add New Task")
                        with gr.Row():
                            new_task_name = gr.Textbox(
                                label="Task Name",
                                placeholder="e.g., Search for OpenAI",
                                scale=2
                            )
                            new_task_priority = gr.Number(
                                label="Priority",
                                value=0,
                                precision=0,
                                scale=1,
                                info="Higher numbers = higher priority"
                            )

                        new_task_description = gr.Textbox(
                            label="Task Description",
                            lines=3,
                            placeholder="Describe what you want the agent to do...",
                        )

                        new_task_additional_info = gr.Textbox(
                            label="Additional Information",
                            lines=2,
                            placeholder="Optional context or instructions...",
                        )

                        with gr.Row():
                            add_task_button = gr.Button("➕ Add to Queue", variant="primary", scale=2)
                            add_and_start_button = gr.Button("➕▶️ Add & Start Queue", variant="secondary", scale=2)

                    # Queue control section
                    with gr.Group():
                        gr.Markdown("#### Queue Controls")
                        with gr.Row():
                            start_queue_button = gr.Button("▶️ Start Queue", variant="primary")
                            pause_queue_button = gr.Button("⏸️ Pause Queue", variant="secondary")
                            resume_queue_button = gr.Button("⏯️ Resume Queue", variant="secondary")
                            stop_queue_button = gr.Button("⏹️ Stop Queue", variant="stop")

                        with gr.Row():
                            clear_completed_button = gr.Button("🗑️ Clear Completed", variant="secondary")
                            reset_browser_button = gr.Button("🔄 Reset Browser", variant="secondary")
                            update_config_button = gr.Button("🔧 Update Config", variant="secondary")

                    # Queue display
                    queue_display = gr.Textbox(
                        label="Queue Status",
                        lines=15,
                        value=get_queue_display(),
                        interactive=False,
                        show_label=True
                    )

                    # Task management section
                    with gr.Group():
                        gr.Markdown("#### Task Management")
                        with gr.Row():
                            task_id_input = gr.Textbox(
                                label="Task ID",
                                placeholder="Enter task ID for operations...",
                                scale=2
                            )
                            with gr.Column(scale=1):
                                move_up_button = gr.Button("⬆️ Move Up")
                                move_down_button = gr.Button("⬇️ Move Down")
                                remove_task_button = gr.Button("🗑️ Remove", variant="stop")

                    # Status message
                    queue_status_message = gr.Textbox(
                        label="Status",
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

            with gr.TabItem("📊 Results", id=8):
                with gr.Group():

                    recording_display = gr.Video(label="Latest Recording")

                    gr.Markdown("### Results")
                    with gr.Row():
                        with gr.Column():
                            final_result_output = gr.Textbox(
                                label="Final Result", lines=3, show_label=True
                            )
                        with gr.Column():
                            errors_output = gr.Textbox(
                                label="Errors", lines=3, show_label=True
                            )
                    with gr.Row():
                        with gr.Column():
                            model_actions_output = gr.Textbox(
                                label="Model Actions", lines=3, show_label=True
                            )
                        with gr.Column():
                            model_thoughts_output = gr.Textbox(
                                label="Model Thoughts", lines=3, show_label=True
                            )

                    trace_file = gr.File(label="Trace File")

                    agent_history_file = gr.File(label="Agent History")

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

            with gr.TabItem("🎥 Recordings", id=9):
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
                    label="Recordings",
                    value=list_recordings(config['save_recording_path']),
                    columns=3,
                    height="auto",
                    object_fit="contain"
                )

                refresh_button = gr.Button("🔄 Refresh Recordings", variant="secondary")
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

    return demo

def main():
    parser = argparse.ArgumentParser(description="Gradio UI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    parser.add_argument("--dark-mode", action="store_true", help="Enable dark mode")
    parser.add_argument("--auto-open", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    config_dict = default_config()
    # Ensure task processor uses the initial configuration so queued tasks
    # have the same settings as the UI right from the start
    task_processor.set_config(config_dict)

    demo = create_ui(config_dict, theme_name=args.theme)
    demo.launch(
        server_name=args.ip,
        server_port=args.port,
        share=False,
        inbrowser=args.auto_open
    )

if __name__ == '__main__':
    main()
