import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    name: str
    description: str
    additional_info: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    model_actions: Optional[str] = None
    model_thoughts: Optional[str] = None
    recording_path: Optional[str] = None
    trace_path: Optional[str] = None
    history_path: Optional[str] = None
    priority: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)

class TaskQueue:
    _instance = None
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._tasks: List[Task] = []
            self._current_task: Optional[Task] = None
            self._is_paused = False
            self._is_running = False
            self._queue_lock = asyncio.Lock()
            self._task_callbacks = []
            self._initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskQueue, cls).__new__(cls)
        return cls._instance
    
    def add_callback(self, callback):
        """Add a callback function to be called when queue state changes"""
        self._task_callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of queue state change"""
        for callback in self._task_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in task queue callback: {e}")
    
    async def add_task(self, name: str, description: str, additional_info: str = "", priority: int = 0) -> str:
        """Add a new task to the queue"""
        async with self._queue_lock:
            task = Task(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                additional_info=additional_info,
                priority=priority
            )
            
            # Insert task based on priority (higher priority first)
            inserted = False
            for i, existing_task in enumerate(self._tasks):
                if task.priority > existing_task.priority:
                    self._tasks.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self._tasks.append(task)
            
            logger.info(f"Added task to queue: {task.name} (ID: {task.id})")
            self._notify_callbacks()
            return task.id
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from the queue"""
        async with self._queue_lock:
            for i, task in enumerate(self._tasks):
                if task.id == task_id and task.status == TaskStatus.PENDING:
                    self._tasks.pop(i)
                    logger.info(f"Removed task from queue: {task.name}")
                    self._notify_callbacks()
                    return True
            return False
    
    async def update_task(self, task_id: str, name: str = None, description: str = None, 
                         additional_info: str = None, priority: int = None) -> bool:
        """Update a pending task"""
        async with self._queue_lock:
            for task in self._tasks:
                if task.id == task_id and task.status == TaskStatus.PENDING:
                    if name is not None:
                        task.name = name
                    if description is not None:
                        task.description = description
                    if additional_info is not None:
                        task.additional_info = additional_info
                    if priority is not None:
                        old_priority = task.priority
                        task.priority = priority
                        # Re-sort if priority changed
                        if old_priority != priority:
                            self._tasks.remove(task)
                            # Re-insert based on new priority
                            inserted = False
                            for i, existing_task in enumerate(self._tasks):
                                if task.priority > existing_task.priority:
                                    self._tasks.insert(i, task)
                                    inserted = True
                                    break
                            if not inserted:
                                self._tasks.append(task)
                    
                    logger.info(f"Updated task: {task.name}")
                    self._notify_callbacks()
                    return True
            return False
    
    async def reorder_task(self, task_id: str, new_position: int) -> bool:
        """Move a task to a new position in the queue"""
        async with self._queue_lock:
            task_index = None
            for i, task in enumerate(self._tasks):
                if task.id == task_id and task.status == TaskStatus.PENDING:
                    task_index = i
                    break
            
            if task_index is not None:
                task = self._tasks.pop(task_index)
                new_position = max(0, min(new_position, len(self._tasks)))
                self._tasks.insert(new_position, task)
                logger.info(f"Reordered task: {task.name} to position {new_position}")
                self._notify_callbacks()
                return True
            return False
    
    async def get_next_task(self) -> Optional[Task]:
        """Get the next pending task"""
        async with self._queue_lock:
            for task in self._tasks:
                if task.status == TaskStatus.PENDING:
                    return task
            return None
    
    async def start_task(self, task_id: str) -> bool:
        """Mark a task as running"""
        async with self._queue_lock:
            for task in self._tasks:
                if task.id == task_id:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now().isoformat()
                    self._current_task = task
                    logger.info(f"Started task: {task.name}")
                    self._notify_callbacks()
                    return True
            return False
    
    async def complete_task(self, task_id: str, result: str = None, error: str = None,
                           model_actions: str = None, model_thoughts: str = None,
                           recording_path: str = None, trace_path: str = None,
                           history_path: str = None) -> bool:
        """Mark a task as completed or failed"""
        async with self._queue_lock:
            for task in self._tasks:
                if task.id == task_id:
                    task.completed_at = datetime.now().isoformat()
                    task.result = result
                    task.error = error
                    task.model_actions = model_actions
                    task.model_thoughts = model_thoughts
                    task.recording_path = recording_path
                    task.trace_path = trace_path
                    task.history_path = history_path
                    
                    if error:
                        task.status = TaskStatus.FAILED
                        logger.error(f"Task failed: {task.name} - {error}")
                    else:
                        task.status = TaskStatus.COMPLETED
                        logger.info(f"Task completed: {task.name}")
                    
                    if self._current_task and self._current_task.id == task_id:
                        self._current_task = None
                    
                    self._notify_callbacks()
                    return True
            return False
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks as dictionaries"""
        return [task.to_dict() for task in self._tasks]
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get only pending tasks"""
        return [task.to_dict() for task in self._tasks if task.status == TaskStatus.PENDING]
    
    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """Get the currently running task"""
        if self._current_task:
            return self._current_task.to_dict()
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        pending_count = len([t for t in self._tasks if t.status == TaskStatus.PENDING])
        running_count = len([t for t in self._tasks if t.status == TaskStatus.RUNNING])
        completed_count = len([t for t in self._tasks if t.status == TaskStatus.COMPLETED])
        failed_count = len([t for t in self._tasks if t.status == TaskStatus.FAILED])
        
        return {
            "total_tasks": len(self._tasks),
            "pending": pending_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count,
            "is_paused": self._is_paused,
            "is_running": self._is_running,
            "current_task": self.get_current_task()
        }
    
    async def pause_queue(self):
        """Pause the queue execution"""
        self._is_paused = True
        logger.info("Task queue paused")
        self._notify_callbacks()
    
    async def resume_queue(self):
        """Resume the queue execution"""
        self._is_paused = False
        logger.info("Task queue resumed")
        self._notify_callbacks()
    
    def is_paused(self) -> bool:
        """Check if queue is paused"""
        return self._is_paused
    
    def is_running(self) -> bool:
        """Check if queue is currently processing tasks"""
        return self._is_running
    
    async def set_running(self, running: bool):
        """Set the running state of the queue"""
        self._is_running = running
        self._notify_callbacks()
    
    async def clear_completed_tasks(self):
        """Remove all completed and failed tasks from the queue"""
        async with self._queue_lock:
            original_count = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]]
            removed_count = original_count - len(self._tasks)
            if removed_count > 0:
                logger.info(f"Cleared {removed_count} completed/failed tasks")
                self._notify_callbacks()
    
    def save_to_file(self, filepath: str):
        """Save queue state to file"""
        try:
            data = {
                "tasks": [task.to_dict() for task in self._tasks],
                "is_paused": self._is_paused,
                "saved_at": datetime.now().isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Queue saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save queue to {filepath}: {e}")
    
    def load_from_file(self, filepath: str):
        """Load queue state from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self._tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
            self._is_paused = data.get("is_paused", False)
            
            # Reset running tasks to pending on load
            for task in self._tasks:
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.PENDING
                    task.started_at = None
            
            self._current_task = None
            logger.info(f"Queue loaded from {filepath}")
            self._notify_callbacks()
        except Exception as e:
            logger.error(f"Failed to load queue from {filepath}: {e}")

# Global task queue instance
task_queue = TaskQueue()
