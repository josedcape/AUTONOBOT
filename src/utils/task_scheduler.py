"""
Advanced Task Scheduler for AUTONOBOT
Handles scheduled task execution with validation and reliability features
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .task_queue import TaskQueue

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    SCHEDULED = "scheduled"

@dataclass
class ScheduledTask:
    """Represents a task with scheduling information"""
    task_id: str
    name: str
    description: str
    additional_info: str
    priority: int
    schedule_type: ScheduleType
    execute_at: datetime
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    is_executed: bool = False
    execution_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'additional_info': self.additional_info,
            'priority': self.priority,
            'schedule_type': self.schedule_type.value,
            'execute_at': self.execute_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'is_executed': self.is_executed,
            'execution_error': self.execution_error
        }

class TaskScheduler:
    """Advanced task scheduler with validation and reliability features"""
    
    _instance = None
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._scheduled_tasks: List[ScheduledTask] = []
            self._task_queue = TaskQueue()
            self._is_running = False
            self._scheduler_thread: Optional[threading.Thread] = None
            self._stop_event = threading.Event()
            self._browser_validator: Optional[Callable] = None
            self._status_callbacks: List[Callable] = []
            self._lock = threading.Lock()
            self._initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskScheduler, cls).__new__(cls)
        return cls._instance
    
    def set_browser_validator(self, validator_func: Callable) -> None:
        """Set function to validate browser session health"""
        self._browser_validator = validator_func
    
    def add_status_callback(self, callback: Callable) -> None:
        """Add callback for status updates"""
        self._status_callbacks.append(callback)
    
    def _notify_status_callbacks(self, message: str, task_id: str = None) -> None:
        """Notify all status callbacks"""
        for callback in self._status_callbacks:
            try:
                callback(message, task_id)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    async def schedule_task(self, name: str, description: str, additional_info: str = "",
                           priority: int = 0, schedule_type: ScheduleType = ScheduleType.IMMEDIATE,
                           execute_at: Optional[datetime] = None) -> str:
        """Schedule a task for execution"""
        
        if schedule_type == ScheduleType.IMMEDIATE:
            execute_at = datetime.now()
        elif execute_at is None:
            raise ValueError("execute_at must be provided for delayed/scheduled tasks")
        
        # Validate future execution time
        if execute_at <= datetime.now() and schedule_type != ScheduleType.IMMEDIATE:
            raise ValueError("Execution time must be in the future")
        
        # Add task to queue immediately for immediate execution
        if schedule_type == ScheduleType.IMMEDIATE:
            task_id = await self._task_queue.add_task(name, description, additional_info, priority)
            self._notify_status_callbacks(f"✅ Tarea '{name}' añadida para ejecución inmediata", task_id)
            return task_id
        
        # Create scheduled task for delayed/scheduled execution
        task_id = f"scheduled_{int(time.time() * 1000)}"
        scheduled_task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            additional_info=additional_info,
            priority=priority,
            schedule_type=schedule_type,
            execute_at=execute_at,
            created_at=datetime.now()
        )
        
        with self._lock:
            self._scheduled_tasks.append(scheduled_task)
            # Sort by execution time
            self._scheduled_tasks.sort(key=lambda x: x.execute_at)
        
        time_str = execute_at.strftime("%Y-%m-%d %H:%M:%S")
        self._notify_status_callbacks(f"⏰ Tarea '{name}' programada para {time_str}", task_id)
        
        # Start scheduler if not running
        if not self._is_running:
            self.start_scheduler()
        
        return task_id
    
    def start_scheduler(self) -> None:
        """Start the task scheduler thread"""
        if self._is_running:
            logger.warning("Task scheduler is already running")
            return
        
        self._is_running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("🕐 Task scheduler started")
        self._notify_status_callbacks("🕐 Programador de tareas iniciado")
    
    def stop_scheduler(self) -> None:
        """Stop the task scheduler"""
        if not self._is_running:
            return
        
        self._is_running = False
        self._stop_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
        
        logger.info("🛑 Task scheduler stopped")
        self._notify_status_callbacks("🛑 Programador de tareas detenido")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop running in separate thread"""
        while self._is_running and not self._stop_event.is_set():
            try:
                self._process_scheduled_tasks()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_scheduled_tasks(self) -> None:
        """Process scheduled tasks that are ready for execution"""
        now = datetime.now()
        tasks_to_execute = []
        
        with self._lock:
            for task in self._scheduled_tasks[:]:  # Copy list to avoid modification during iteration
                if not task.is_executed and task.execute_at <= now:
                    tasks_to_execute.append(task)
        
        for task in tasks_to_execute:
            self._execute_scheduled_task(task)
    
    def _execute_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Execute a scheduled task with validation and retry logic"""
        try:
            # Validate browser session if validator is available
            if self._browser_validator:
                try:
                    browser_healthy = self._browser_validator()
                    if not browser_healthy:
                        logger.warning(f"Browser session unhealthy for task {scheduled_task.name}")
                        self._notify_status_callbacks(f"⚠️ Sesión de navegador no saludable para tarea '{scheduled_task.name}'", scheduled_task.task_id)
                        self._retry_scheduled_task(scheduled_task, "Browser session unhealthy")
                        return
                except Exception as e:
                    logger.error(f"Browser validation failed: {e}")
                    self._retry_scheduled_task(scheduled_task, f"Browser validation failed: {e}")
                    return
            
            # Add task to execution queue
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                task_id = loop.run_until_complete(
                    self._task_queue.add_task(
                        scheduled_task.name,
                        scheduled_task.description,
                        scheduled_task.additional_info,
                        scheduled_task.priority
                    )
                )
                
                # Mark as executed
                with self._lock:
                    scheduled_task.is_executed = True
                    scheduled_task.task_id = task_id  # Update with actual queue task ID
                
                logger.info(f"✅ Scheduled task executed: {scheduled_task.name} (ID: {task_id})")
                self._notify_status_callbacks(f"✅ Tarea programada ejecutada: '{scheduled_task.name}'", task_id)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to execute scheduled task {scheduled_task.name}: {e}")
            self._retry_scheduled_task(scheduled_task, str(e))
    
    def _retry_scheduled_task(self, scheduled_task: ScheduledTask, error: str) -> None:
        """Retry a failed scheduled task"""
        scheduled_task.retry_count += 1
        scheduled_task.execution_error = error
        
        if scheduled_task.retry_count < scheduled_task.max_retries:
            # Retry in 30 seconds
            scheduled_task.execute_at = datetime.now() + timedelta(seconds=30)
            logger.info(f"🔄 Retrying scheduled task {scheduled_task.name} in 30 seconds (attempt {scheduled_task.retry_count + 1}/{scheduled_task.max_retries})")
            self._notify_status_callbacks(f"🔄 Reintentando tarea '{scheduled_task.name}' en 30 segundos", scheduled_task.task_id)
        else:
            # Max retries reached, mark as failed
            with self._lock:
                scheduled_task.is_executed = True  # Don't retry anymore
            logger.error(f"❌ Scheduled task {scheduled_task.name} failed after {scheduled_task.max_retries} retries")
            self._notify_status_callbacks(f"❌ Tarea '{scheduled_task.name}' falló después de {scheduled_task.max_retries} intentos", scheduled_task.task_id)
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled tasks"""
        with self._lock:
            return [task.to_dict() for task in self._scheduled_tasks]
    
    def get_pending_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of pending scheduled tasks"""
        with self._lock:
            return [task.to_dict() for task in self._scheduled_tasks if not task.is_executed]
    
    def cancel_scheduled_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        with self._lock:
            for task in self._scheduled_tasks:
                if task.task_id == task_id and not task.is_executed:
                    self._scheduled_tasks.remove(task)
                    logger.info(f"🚫 Cancelled scheduled task: {task.name}")
                    self._notify_status_callbacks(f"🚫 Tarea programada cancelada: '{task.name}'", task_id)
                    return True
        return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        with self._lock:
            pending_tasks = [t for t in self._scheduled_tasks if not t.is_executed]
            executed_tasks = [t for t in self._scheduled_tasks if t.is_executed]
            
            return {
                'is_running': self._is_running,
                'total_scheduled': len(self._scheduled_tasks),
                'pending': len(pending_tasks),
                'executed': len(executed_tasks),
                'next_execution': pending_tasks[0].execute_at.isoformat() if pending_tasks else None
            }

# Global scheduler instance
task_scheduler = TaskScheduler()
