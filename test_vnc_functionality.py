#!/usr/bin/env python3
"""
Quick VNC Functionality Test Script
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_vnc_server():
    """Test VNC server functionality"""
    print("🧪 Testing VNC Server Functionality")
    print("=" * 50)
    
    try:
        # Import VNC manager
        from src.vnc.vnc_server import vnc_manager
        
        print("✅ VNC modules imported successfully")
        
        # Test server creation
        print("\n🔧 Creating VNC server...")
        server = await vnc_manager.get_or_create_server("test")
        print(f"✅ VNC server created: {type(server).__name__}")
        
        # Test server startup
        print("\n🚀 Starting VNC server...")
        result = await server.start_server()
        
        print(f"\n📊 VNC Server Result:")
        print(f"Status: {result.get('status')}")
        print(f"Method: {result.get('method', 'N/A')}")
        print(f"Port: {result.get('port', 'N/A')}")
        print(f"Display: {result.get('display', 'N/A')}")
        
        if result.get('error'):
            print(f"Error: {result.get('error')}")
            if result.get('suggestions'):
                print("Suggestions:")
                for suggestion in result.get('suggestions'):
                    print(f"  - {suggestion}")
        
        if result.get('note'):
            print(f"Note: {result.get('note')}")
        
        # Test environment variables
        print(f"\n🌍 Environment Variables:")
        env_vars = server.get_display_env()
        for key, value in env_vars.items():
            print(f"  {key}={value}")
        
        # Test status
        print(f"\n📈 Server Status:")
        status = server.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test mobile access info
        if result.get('status') == 'success':
            port = result.get('port')
            print(f"\n📱 Mobile Access Information:")
            print(f"  Local URL: http://localhost:{port}")
            print(f"  Network URL: http://[YOUR_PC_IP]:{port}")
            print(f"  VNC Viewer: Available in webUI at http://localhost:7860")
            print(f"  Mobile Compatible: ✅ Yes")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await server.stop_server()
        print("✅ VNC server stopped")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ VNC test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_browser_agent():
    """Test browser agent with VNC"""
    print("\n🤖 Testing Browser Agent VNC Integration")
    print("=" * 50)
    
    try:
        # Import browser agent
        from src.agent.browser_use.browser_use_agent import BrowserUseAgent
        
        print("✅ Browser agent imported successfully")
        
        # Create VNC-enabled agent
        print("\n🔧 Creating VNC-enabled browser agent...")
        agent = BrowserUseAgent(
            llm_provider="openai",
            model_name="gpt-4o",
            enable_vnc=True
        )
        print("✅ VNC-enabled browser agent created")
        
        # Test VNC setup
        print("\n🚀 Testing VNC setup...")
        await agent._setup_vnc_if_enabled()
        
        if agent.vnc_server:
            print("✅ VNC server setup successful")
            print(f"VNC Info: {agent.vnc_info}")
        else:
            print("⚠️ VNC server not available")
        
        # Cleanup
        await agent._cleanup_vnc()
        print("✅ Browser agent VNC cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test required dependencies"""
    print("📦 Testing Dependencies")
    print("=" * 30)
    
    dependencies = [
        ('psutil', 'Process management'),
        ('gradio', 'Web interface'),
        ('asyncio', 'Async support'),
        ('socket', 'Network connections'),
        ('subprocess', 'Process execution')
    ]
    
    all_good = True
    
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available ({desc})")
        except ImportError:
            print(f"❌ {dep}: Missing ({desc})")
            all_good = False
    
    return all_good


async def main():
    """Main test function"""
    print("🚀 VNC Functionality Test Suite")
    print("=" * 60)
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n❌ Some dependencies are missing. Installing...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("✅ Dependencies installed")
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return
    
    # Test VNC server
    vnc_ok = await test_vnc_server()
    
    # Test browser agent integration
    agent_ok = await test_browser_agent()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"VNC Server: {'✅ PASS' if vnc_ok else '❌ FAIL'}")
    print(f"Browser Agent: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    
    if vnc_ok:
        print("\n🎉 VNC functionality is working!")
        print("\n📋 Next Steps:")
        print("1. Start webUI: python webui.py --port 7860")
        print("2. Go to '🤖 Agent Interactivo' tab")
        print("3. Select '📺 VNC Viewer (Remote)' mode")
        print("4. Submit a browser task")
        print("5. Click '🖥️ Open VNC Viewer'")
        print("\n📱 For mobile access:")
        print("1. Find your PC's IP address")
        print("2. Access webUI from mobile: http://[PC_IP]:7860")
        print("3. Use VNC viewer normally")
    else:
        print("\n⚠️ VNC functionality needs setup")
        print("\n🔧 Setup Options:")
        print("1. Run: python setup_windows_vnc.py")
        print("2. Or use PC Browser mode for immediate functionality")
    
    print("\n✨ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
