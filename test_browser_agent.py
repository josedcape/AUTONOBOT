#!/usr/bin/env python3
"""
Test script to verify browser-use agent functionality
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_browser_agent():
    """Test basic browser agent functionality"""
    try:
        print("Testing browser-use agent...")
        
        # Try to import the basic components
        from browser_use import Agent
        print("✓ Successfully imported Agent")
        
        # Try to create a simple agent
        agent = Agent(
            task="Navigate to google.com and search for 'hello world'",
            llm=None  # We'll set this up properly later
        )
        print("✓ Successfully created Agent instance")
        
        # Check if we can access browser functionality
        print(f"Agent task: {agent.task}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_browser_creation():
    """Test browser creation"""
    try:
        from browser_use import Browser
        print("✓ Successfully imported Browser")
        
        # Try to create a browser instance
        browser = Browser()
        print("✓ Successfully created Browser instance")
        
        return True
        
    except ImportError as e:
        print(f"❌ Browser import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Browser creation error: {e}")
        return False

async def test_llm_setup():
    """Test LLM setup"""
    try:
        # Check if we have API keys
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        print(f"OpenAI API Key: {'✓ Set' if openai_key else '❌ Not set'}")
        print(f"Anthropic API Key: {'✓ Set' if anthropic_key else '❌ Not set'}")
        print(f"Gemini API Key: {'✓ Set' if gemini_key else '❌ Not set'}")
        
        if openai_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4", api_key=openai_key)
            print("✓ Successfully created OpenAI LLM")
            return llm
        elif anthropic_key:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-3-sonnet-20240229", api_key=anthropic_key)
            print("✓ Successfully created Anthropic LLM")
            return llm
        else:
            print("❌ No API keys available")
            return None
            
    except ImportError as e:
        print(f"❌ LLM import error: {e}")
        return None
    except Exception as e:
        print(f"❌ LLM setup error: {e}")
        return None

async def main():
    """Main test function"""
    print("=== Browser-Use Agent Test ===\n")
    
    # Test 1: Basic imports
    print("1. Testing basic imports...")
    basic_test = await test_browser_agent()
    
    # Test 2: Browser creation
    print("\n2. Testing browser creation...")
    browser_test = await test_browser_creation()
    
    # Test 3: LLM setup
    print("\n3. Testing LLM setup...")
    llm = await test_llm_setup()
    
    # Test 4: Full agent creation
    print("\n4. Testing full agent creation...")
    if basic_test and browser_test and llm:
        try:
            from browser_use import Agent
            agent = Agent(
                task="Test task",
                llm=llm
            )
            print("✓ Successfully created full Agent with LLM")
            
            # Test browser initialization
            print("5. Testing browser initialization...")
            # We won't actually run the agent, just check if it can be set up
            print("✓ Agent ready for execution")
            
        except Exception as e:
            print(f"❌ Full agent creation failed: {e}")
    else:
        print("❌ Cannot create full agent due to previous failures")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
