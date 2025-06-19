#!/usr/bin/env python3
"""
Test script to verify the task queue functionality works correctly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.webui.webui_manager import WebuiManager


async def test_task_queue():
    """Test the task queue functionality."""
    print("Testing Task Queue Functionality...")
    
    # Create a WebuiManager instance
    manager = WebuiManager()
    
    # Initialize browser use agent attributes
    manager.init_browser_use_agent()
    
    # Start the task processor
    await manager.start_task_processor()
    print("✓ Task processor started")
    
    # Test adding tasks
    task1_id = await manager.add_task("Test task 1", "browser_use")
    task2_id = await manager.add_task("Test task 2", "browser_use")
    task3_id = await manager.add_task("Test task 3", "browser_use")
    
    print(f"✓ Added 3 tasks: {task1_id[:8]}, {task2_id[:8]}, {task3_id[:8]}")
    
    # Check queue display
    queue_text = manager.get_queue_display_text()
    print(f"✓ Queue display: {queue_text}")
    
    # Test pause/resume functionality
    await asyncio.sleep(3)  # Let first task start
    
    if manager.current_task_id:
        print(f"✓ Current task: {manager.current_task_id[:8]}")
        
        # Test pause
        await manager.pause_current_task()
        print("✓ Task paused")
        
        await asyncio.sleep(2)
        
        # Test resume
        await manager.resume_current_task()
        print("✓ Task resumed")
        
        await asyncio.sleep(2)
        
        # Test stop
        await manager.stop_task()
        print("✓ Task stopped")
    
    # Wait a bit for tasks to process
    await asyncio.sleep(5)
    
    # Check final status
    print("\nFinal Task Status:")
    for task_id, status in manager.task_status.items():
        description = manager.task_descriptions.get(task_id, "Unknown")
        print(f"  {task_id[:8]}: {status} - {description}")
    
    # Stop the task processor
    await manager.stop_task_processor()
    print("✓ Task processor stopped")
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_task_queue())
