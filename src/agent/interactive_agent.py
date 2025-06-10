import asyncio
import logging
from typing import Optional, List, Dict, Any
from src.utils.agent_state import AgentState, AgentStatus, ChatMessage
from src.agent.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

class InteractiveAgent:
    """
    Interactive agent that can handle real-time chat commands and task switching
    """
    
    def __init__(self, base_agent: CustomAgent):
        self.base_agent = base_agent
        self.agent_state = AgentState()
        self.current_execution_task = None
        self.is_running = False
        
    async def run_interactive(self, initial_task: str, max_steps: int = 100) -> Dict[str, Any]:
        """
        Run the agent in interactive mode with chat-based control
        """
        self.is_running = True
        self.agent_state.set_status(AgentStatus.RUNNING)
        self.agent_state.current_task = initial_task
        
        # Add initial task to chat history
        self.agent_state.add_chat_message(f"Starting task: {initial_task}", "agent")
        
        try:
            result = await self._execute_with_interrupts(initial_task, max_steps)
            return result
        finally:
            self.is_running = False
            self.agent_state.set_status(AgentStatus.IDLE)
    
    async def _execute_with_interrupts(self, task: str, max_steps: int) -> Dict[str, Any]:
        """
        Execute task with support for interrupts and task switching
        """
        current_task = task
        all_results = []
        all_errors = []
        all_actions = []
        all_thoughts = []
        
        while self.is_running and not self.agent_state.is_stop_requested():
            try:
                # Check for pause requests
                if self.agent_state.is_pause_requested():
                    logger.info("🔄 Agent paused, waiting for resume...")
                    self.agent_state.add_chat_message("Agent paused. Send 'resume' to continue.", "agent")
                    await self._wait_for_resume()
                    continue
                
                # Check for task switch requests
                if self.agent_state.is_task_switch_requested():
                    new_task = self.agent_state.get_pending_task()
                    logger.info(f"🔄 Switching task from '{current_task}' to '{new_task}'")
                    self.agent_state.add_chat_message(f"Switching to new task: {new_task}", "agent")
                    current_task = new_task
                    self.agent_state.clear_task_switch()
                
                # Execute current task with interrupt checking
                logger.info(f"🚀 Executing task: {current_task[:50]}...")
                result = await self._execute_task_with_monitoring(current_task, max_steps)
                
                if result:
                    all_results.append(result.get('final_result', ''))
                    all_errors.extend(result.get('errors', []))
                    all_actions.extend(result.get('actions', []))
                    all_thoughts.extend(result.get('thoughts', []))
                
                # Check if we should continue or if this was a one-time task
                if not self.agent_state.is_task_switch_requested():
                    break
                    
            except Exception as e:
                error_msg = f"Error executing task '{current_task}': {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                self.agent_state.add_chat_message(f"Error: {error_msg}", "agent")
                break
        
        # Compile final results
        final_result = {
            'final_result': '\n\n'.join(all_results) if all_results else "No results",
            'errors': all_errors,
            'actions': all_actions,
            'thoughts': all_thoughts,
            'chat_history': self.agent_state.get_chat_history(),
            'status': self.agent_state.get_status().value
        }
        
        return final_result
    
    async def _execute_task_with_monitoring(self, task: str, max_steps: int) -> Optional[Dict[str, Any]]:
        """
        Execute a single task while monitoring for interrupts
        """
        # Create a task for the agent execution
        self.current_execution_task = asyncio.create_task(
            self._run_base_agent(task, max_steps)
        )
        
        # Create a task for monitoring interrupts
        monitor_task = asyncio.create_task(
            self._monitor_interrupts()
        )
        
        try:
            # Wait for either the agent to complete or an interrupt
            done, pending = await asyncio.wait(
                [self.current_execution_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Get the result from the completed task
            if self.current_execution_task in done:
                return await self.current_execution_task
            else:
                # Interrupt occurred
                logger.info("🔄 Task interrupted by user command")
                return None
                
        except Exception as e:
            logger.error(f"Error in task execution: {e}")
            return None
        finally:
            self.current_execution_task = None
    
    async def _run_base_agent(self, task: str, max_steps: int) -> Dict[str, Any]:
        """
        Run the base agent with the given task
        """
        try:
            # Use the base agent's run method
            history = await self.base_agent.run(max_steps=max_steps)
            
            return {
                'final_result': history.final_result(),
                'errors': history.errors(),
                'actions': history.model_actions(),
                'thoughts': history.model_thoughts()
            }
        except Exception as e:
            logger.error(f"Base agent execution error: {e}")
            return {
                'final_result': f"Agent execution failed: {str(e)}",
                'errors': [str(e)],
                'actions': [],
                'thoughts': []
            }
    
    async def _monitor_interrupts(self):
        """
        Monitor for user interrupts and commands
        """
        while self.is_running:
            try:
                # Check for task switch requests
                new_task = await self.agent_state.get_next_task_switch()
                if new_task:
                    logger.info(f"🔄 Task switch detected: {new_task}")
                    # Cancel current execution
                    if self.current_execution_task and not self.current_execution_task.done():
                        self.current_execution_task.cancel()
                    return
                
                # Check for stop requests
                if self.agent_state.is_stop_requested():
                    logger.info("🛑 Stop request detected")
                    if self.current_execution_task and not self.current_execution_task.done():
                        self.current_execution_task.cancel()
                    return
                
                # Check for pause requests
                if self.agent_state.is_pause_requested():
                    logger.info("⏸️ Pause request detected")
                    if self.current_execution_task and not self.current_execution_task.done():
                        self.current_execution_task.cancel()
                    return
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in interrupt monitoring: {e}")
                await asyncio.sleep(1)
    
    async def _wait_for_resume(self):
        """
        Wait for resume command while paused
        """
        while self.agent_state.is_pause_requested() and not self.agent_state.is_stop_requested():
            await asyncio.sleep(0.5)
    
    def send_chat_message(self, message: str) -> ChatMessage:
        """
        Send a chat message and process any commands
        """
        return self.agent_state.add_chat_message(message, "user")
    
    def get_chat_history(self) -> List[Dict]:
        """
        Get the current chat history
        """
        return self.agent_state.get_chat_history()
    
    def get_status(self) -> str:
        """
        Get the current agent status
        """
        return self.agent_state.get_status().value
    
    def stop(self):
        """
        Stop the interactive agent
        """
        self.agent_state.request_stop()
        if self.current_execution_task and not self.current_execution_task.done():
            self.current_execution_task.cancel()
    
    def pause(self):
        """
        Pause the interactive agent
        """
        self.agent_state.request_pause()
    
    def resume(self):
        """
        Resume the interactive agent
        """
        self.agent_state.request_resume()
    
    def switch_task(self, new_task: str):
        """
        Switch to a new task
        """
        self.agent_state.request_task_switch(new_task)
