#!/usr/bin/env python3
"""
Test browser integration with the task queue system
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_browser_agent():
    """Test the BrowserUseAgent functionality"""
    try:
        print("🧪 Testing BrowserUseAgent integration...")
        
        # Import the agent
        from src.agent.browser_use.browser_use_agent import BrowserUseAgent
        
        # Create agent instance
        agent = BrowserUseAgent(llm_provider="openai", model_name="gpt-4")
        print("✅ Agent created successfully")
        
        # Test a simple task
        task = "Navigate to google.com and search for 'hello world'"
        print(f"🚀 Executing task: {task}")
        
        result = await agent.execute_task(task, max_steps=10)
        
        print(f"📊 Task result: {result}")
        
        if result.get("success"):
            print("✅ Browser automation test PASSED!")
        else:
            print(f"❌ Browser automation test FAILED: {result.get('error')}")
            
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_queue_integration():
    """Test the task queue integration"""
    try:
        print("\n🧪 Testing task queue integration...")
        
        # Import the webui manager
        from src.webui.webui_manager import WebuiManager
        
        # Create manager instance
        manager = WebuiManager()
        print("✅ WebuiManager created successfully")
        
        # Start task processor
        await manager.start_task_processor()
        print("✅ Task processor started")
        
        # Add a test task
        task_id = await manager.add_task("Navigate to example.com")
        print(f"✅ Task added with ID: {task_id}")
        
        # Wait a bit for processing
        await asyncio.sleep(5)
        
        # Check task status
        status = manager.task_status.get(task_id, "unknown")
        print(f"📊 Task status: {status}")
        
        # Stop task processor
        await manager.stop_task_processor()
        print("✅ Task processor stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🔬 Browser Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Browser Agent
    browser_test = await test_browser_agent()
    
    # Test 2: Task Queue Integration
    queue_test = await test_task_queue_integration()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"Browser Agent: {'✅ PASS' if browser_test else '❌ FAIL'}")
    print(f"Task Queue: {'✅ PASS' if queue_test else '❌ FAIL'}")
    
    if browser_test and queue_test:
        print("\n🎉 All tests PASSED! Browser automation is working!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
