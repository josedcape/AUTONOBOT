import asyncio
import logging
from typing import Optional, Callable, Any
from .task_queue import task_queue, TaskStatus
from ..utils import utils

logger = logging.getLogger(__name__)

class TaskProcessor:
    _instance = None
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._is_processing = False
            self._processing_task = None
            self._stop_processing = False
            self._agent_runner_func: Optional[Callable] = None
            self._config = {}
            self._initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskProcessor, cls).__new__(cls)
        return cls._instance
    
    def set_agent_runner(self, runner_func: Callable):
        """Set the function that will run individual tasks"""
        self._agent_runner_func = runner_func
    
    def set_config(self, config: dict):
        """Set the configuration for task execution"""
        self._config = config.copy()
    
    async def start_processing(self):
        """Start processing tasks from the queue"""
        if self._is_processing:
            logger.warning("Task processor is already running")
            return

        if not self._agent_runner_func:
            logger.error("No agent runner function set")
            return

        self._is_processing = True
        self._stop_processing = False
        await task_queue.set_running(True)

        logger.info("Started task queue processing")

        try:
            while self._is_processing and not self._stop_processing:
                try:
                    # Check if queue is paused
                    if task_queue.is_paused():
                        await asyncio.sleep(1)
                        continue

                    # Get next task
                    next_task = await task_queue.get_next_task()
                    if not next_task:
                        # No pending tasks, wait a bit and check again
                        await asyncio.sleep(2)
                        continue

                    # Start the task
                    await task_queue.start_task(next_task.id)
                    self._processing_task = next_task

                    logger.info(f"Processing task: {next_task.name}")

                    try:
                        # Execute the task with proper error handling
                        result = await self._execute_task_safely(next_task)

                        # Mark task as completed
                        await task_queue.complete_task(
                            next_task.id,
                            result=result.get('final_result', ''),
                            error=result.get('errors', ''),
                            model_actions=result.get('model_actions', ''),
                            model_thoughts=result.get('model_thoughts', ''),
                            recording_path=result.get('recording_path'),
                            trace_path=result.get('trace_path'),
                            history_path=result.get('history_path')
                        )

                    except Exception as e:
                        logger.error(f"Task execution failed: {e}")
                        await task_queue.complete_task(
                            next_task.id,
                            error=str(e)
                        )

                    finally:
                        self._processing_task = None

                    # Small delay between tasks
                    await asyncio.sleep(0.5)

                except asyncio.CancelledError:
                    logger.info("Task processing was cancelled")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in task processing loop: {e}")
                    await asyncio.sleep(1)  # Wait before retrying

        except Exception as e:
            logger.error(f"Task processor error: {e}")

        finally:
            self._is_processing = False
            await task_queue.set_running(False)
            logger.info("Stopped task queue processing")
    
    async def stop_processing(self):
        """Stop processing tasks"""
        self._stop_processing = True
        if self._processing_task:
            logger.info("Stopping current task...")
            # The agent should handle stop requests through the global agent state

        # Wait for current task to finish with timeout
        timeout = 30  # 30 seconds timeout
        while self._is_processing and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

        if self._is_processing:
            logger.warning("Task processor did not stop gracefully within timeout")
        else:
            logger.info("Task processor stopped")

    async def _execute_task_safely(self, task) -> dict:
        """Execute a task with proper error handling and cleanup"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return await self._execute_task(task)
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                logger.error(f"Error executing task {task.name} (attempt {retry_count}/{max_retries}): {error_msg}")

                # Check if it's a browser connection error
                browser_error_keywords = [
                    "Browser closed",
                    "TargetClosedError",
                    "Connection error",
                    "Target page",
                    "browser has been closed",
                    "no valid pages available",
                    "Page.evaluate: Target page"
                ]

                is_browser_error = any(keyword in error_msg for keyword in browser_error_keywords)

                if is_browser_error:
                    if retry_count < max_retries:
                        logger.info(f"🔄 Browser error detected, waiting before retry {retry_count + 1}: {error_msg}")
                        await asyncio.sleep(2)  # Wait before retry
                        continue

                # If it's the last retry or a non-recoverable error, return error result
                if retry_count >= max_retries:
                    return {
                        'final_result': '',
                        'errors': f"Failed after {max_retries} attempts: {error_msg}",
                        'model_actions': '',
                        'model_thoughts': '',
                        'recording_path': None,
                        'trace_path': None,
                        'history_path': None
                    }

        # This should never be reached, but just in case
        return {
            'final_result': '',
            'errors': 'Unknown error occurred',
            'model_actions': '',
            'model_thoughts': '',
            'recording_path': None,
            'trace_path': None,
            'history_path': None
        }

    async def _execute_task(self, task) -> dict:
        """Execute a single task using the configured agent runner"""
        if not self._agent_runner_func:
            raise Exception("No agent runner function configured")
        
        # Prepare task configuration
        task_config = self._config.copy()
        task_config.update({
            'task': task.description,
            'add_infos': task.additional_info,
            'keep_browser_open': True,  # Always keep browser open for queue processing
        })

        # Force browser persistence for queue processing
        task_config['keep_browser_open'] = True
        
        # Execute the task
        result = await self._agent_runner_func(
            agent_type=task_config.get('agent_type', 'custom'),
            llm_provider=task_config.get('llm_provider', 'openai'),
            llm_model_name=task_config.get('llm_model_name', 'gpt-4o'),
            llm_temperature=task_config.get('llm_temperature', 1.0),
            llm_base_url=task_config.get('llm_base_url', ''),
            llm_api_key=task_config.get('llm_api_key', ''),
            use_own_browser=task_config.get('use_own_browser', False),
            keep_browser_open=True,  # Always keep browser open
            headless=task_config.get('headless', False),
            disable_security=task_config.get('disable_security', True),
            window_w=task_config.get('window_w', 1280),
            window_h=task_config.get('window_h', 1100),
            save_recording_path=task_config.get('save_recording_path', './tmp/record_videos'),
            save_agent_history_path=task_config.get('save_agent_history_path', './tmp/agent_history'),
            save_trace_path=task_config.get('save_trace_path', './tmp/traces'),
            enable_recording=task_config.get('enable_recording', True),
            task=task.description,
            add_infos=task.additional_info,
            max_steps=task_config.get('max_steps', 100),
            use_vision=task_config.get('use_vision', True),
            max_actions_per_step=task_config.get('max_actions_per_step', 10),
            tool_calling_method=task_config.get('tool_calling_method', 'auto')
        )
        
        # Parse result tuple
        if isinstance(result, tuple) and len(result) >= 7:
            return {
                'final_result': result[0] or '',
                'errors': result[1] or '',
                'model_actions': result[2] or '',
                'model_thoughts': result[3] or '',
                'recording_path': result[4],
                'trace_path': result[5],
                'history_path': result[6]
            }
        else:
            return {
                'final_result': str(result) if result else '',
                'errors': '',
                'model_actions': '',
                'model_thoughts': '',
                'recording_path': None,
                'trace_path': None,
                'history_path': None
            }
    
    def is_processing(self) -> bool:
        """Check if processor is currently running"""
        return self._is_processing
    
    def get_current_task(self):
        """Get the currently processing task"""
        return self._processing_task

# Global task processor instance
task_processor = TaskProcessor()
