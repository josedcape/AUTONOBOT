#!/usr/bin/env python3
"""
Simple test to check browser-use functionality
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    try:
        print("Testing browser-use imports...")
        
        # Test basic import
        from browser_use import Agent
        print("✓ Agent imported successfully")
        
        # Test LLM setup
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4", api_key=openai_key)
            print("✓ LLM created successfully")
            
            # Create agent
            agent = Agent(
                task="Navigate to google.com",
                llm=llm
            )
            print("✓ Agent created successfully")
            print(f"Task: {agent.task}")
            
        else:
            print("❌ No OpenAI API key found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
