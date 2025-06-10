import asyncio
import time
from typing import List, Dict, Optional
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    SWITCHING_TASK = "switching_task"

class ChatMessage:
    def __init__(self, content: str, sender: str = "user", timestamp: float = None):
        self.content = content
        self.sender = sender  # "user" or "agent"
        self.timestamp = timestamp or time.time()
        self.message_type = self._classify_message()

    def _classify_message(self):
        """Classify the message type for command recognition"""
        content_lower = self.content.lower().strip()

        # Control commands
        if any(cmd in content_lower for cmd in ["pause", "stop for now", "wait"]):
            return "pause"
        elif any(cmd in content_lower for cmd in ["resume", "continue", "go on"]):
            return "resume"
        elif any(cmd in content_lower for cmd in ["cancel", "stop completely", "abort"]):
            return "cancel"
        elif any(cmd in content_lower for cmd in ["now do", "switch to", "instead", "change task"]):
            return "task_switch"
        else:
            return "task"

class AgentState:
    _instance = None

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._stop_requested = asyncio.Event()
            self._pause_requested = asyncio.Event()
            self._task_switch_requested = asyncio.Event()
            self.last_valid_state = None
            self.status = AgentStatus.IDLE
            self.chat_history: List[ChatMessage] = []
            self.current_task = ""
            self.pending_task = ""
            self.task_switch_queue = asyncio.Queue()
            self._initialized = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentState, cls).__new__(cls)
        return cls._instance

    # Original methods
    def request_stop(self):
        self._stop_requested.set()
        self.status = AgentStatus.STOPPING

    def clear_stop(self):
        self._stop_requested.clear()
        self.last_valid_state = None
        if self.status == AgentStatus.STOPPING:
            self.status = AgentStatus.IDLE

    def is_stop_requested(self):
        return self._stop_requested.is_set()

    def should_stop(self):
        return self.is_stop_requested()

    def set_last_valid_state(self, state):
        self.last_valid_state = state

    def get_last_valid_state(self):
        return self.last_valid_state

    # New chat-based control methods
    def add_chat_message(self, content: str, sender: str = "user") -> ChatMessage:
        """Add a new chat message and process any commands"""
        message = ChatMessage(content, sender)
        self.chat_history.append(message)

        if sender == "user":
            self._process_user_command(message)

        return message

    def _process_user_command(self, message: ChatMessage):
        """Process user commands from chat messages"""
        if message.message_type == "pause":
            self.request_pause()
        elif message.message_type == "resume":
            self.request_resume()
        elif message.message_type == "cancel":
            self.request_stop()
        elif message.message_type == "task_switch":
            # Extract new task from message
            new_task = self._extract_new_task(message.content)
            if new_task:
                self.request_task_switch(new_task)

    def _extract_new_task(self, content: str) -> str:
        """Extract new task from task switch command"""
        content_lower = content.lower()

        # Look for patterns like "now do X", "switch to X", "instead X"
        patterns = [
            "now do ",
            "switch to ",
            "instead ",
            "change task to ",
            "do this instead: ",
            "stop that and "
        ]

        for pattern in patterns:
            if pattern in content_lower:
                # Extract everything after the pattern
                start_idx = content_lower.find(pattern) + len(pattern)
                new_task = content[start_idx:].strip()
                return new_task

        # If no pattern found, treat the whole message as a new task
        return content.strip()

    def request_pause(self):
        """Request agent to pause"""
        self._pause_requested.set()
        self.status = AgentStatus.PAUSED

    def request_resume(self):
        """Request agent to resume"""
        self._pause_requested.clear()
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.RUNNING

    def is_pause_requested(self):
        return self._pause_requested.is_set()

    def request_task_switch(self, new_task: str):
        """Request to switch to a new task"""
        self.pending_task = new_task
        self._task_switch_requested.set()
        self.status = AgentStatus.SWITCHING_TASK
        # Add to queue for processing
        try:
            self.task_switch_queue.put_nowait(new_task)
        except asyncio.QueueFull:
            pass

    def is_task_switch_requested(self):
        return self._task_switch_requested.is_set()

    def get_pending_task(self) -> str:
        return self.pending_task

    def clear_task_switch(self):
        """Clear task switch request and update current task"""
        self._task_switch_requested.clear()
        if self.pending_task:
            self.current_task = self.pending_task
            self.pending_task = ""
        if self.status == AgentStatus.SWITCHING_TASK:
            self.status = AgentStatus.RUNNING

    async def get_next_task_switch(self) -> Optional[str]:
        """Get the next task switch from the queue"""
        try:
            return await asyncio.wait_for(self.task_switch_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    def get_chat_history(self) -> List[Dict]:
        """Get chat history in a format suitable for UI"""
        return [
            {
                "content": msg.content,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "type": msg.message_type
            }
            for msg in self.chat_history
        ]

    def clear_chat_history(self):
        """Clear chat history"""
        self.chat_history.clear()

    def set_status(self, status: AgentStatus):
        """Set agent status"""
        self.status = status

    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        return self.status

    def reset(self):
        """Reset all state"""
        self.clear_stop()
        self._pause_requested.clear()
        self._task_switch_requested.clear()
        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.pending_task = ""
        # Clear the queue
        while not self.task_switch_queue.empty():
            try:
                self.task_switch_queue.get_nowait()
            except asyncio.QueueEmpty:
                break