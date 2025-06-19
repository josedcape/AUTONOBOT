#!/usr/bin/env python3
"""
Windows VNC Setup Assistant - Automatically configure VNC for Windows
"""

import subprocess
import sys
import platform
import os
import time


def run_command(command, description="", timeout=300):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}")
    print(f"Running: {command}")
    
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)
        
        print(f"✅ Success: {description}")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False, e.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {description}")
        return False, "Command timed out"


def check_wsl_status():
    """Check WSL installation status"""
    print("\n🔍 Checking WSL status...")
    
    # Check if WSL is installed
    success, output = run_command(['wsl', '--list'], "Checking WSL installation")
    if not success:
        return "not_installed"
    
    # Check if any distributions are installed
    if 'Ubuntu' in output or 'Debian' in output:
        print("✅ WSL with Linux distribution found")
        
        # Check if VNC packages are installed
        success, _ = run_command(['wsl', 'bash', '-c', 'which xvfb-run && which x11vnc'], "Checking VNC packages in WSL")
        if success:
            return "ready"
        else:
            return "needs_packages"
    else:
        return "no_distro"


def check_docker_status():
    """Check Docker installation status"""
    print("\n🔍 Checking Docker status...")
    
    success, output = run_command(['docker', '--version'], "Checking Docker installation")
    if success:
        print("✅ Docker found")
        
        # Check if Docker is running
        success, _ = run_command(['docker', 'ps'], "Checking Docker daemon")
        if success:
            return "ready"
        else:
            return "not_running"
    else:
        return "not_installed"


def install_wsl():
    """Install WSL and Ubuntu"""
    print("\n🐧 Installing WSL and Ubuntu...")
    
    print("📋 This will:")
    print("1. Enable WSL feature")
    print("2. Install Ubuntu distribution")
    print("3. Set up VNC packages")
    
    response = input("\nProceed with WSL installation? (y/N): ").lower()
    if response != 'y':
        print("❌ WSL installation cancelled")
        return False
    
    # Install WSL
    print("\n🔧 Installing WSL (this may take several minutes)...")
    success, output = run_command(['wsl', '--install'], "Installing WSL", timeout=600)
    
    if not success:
        print("❌ WSL installation failed")
        print("💡 Try running as Administrator or install manually:")
        print("   1. Open PowerShell as Administrator")
        print("   2. Run: wsl --install")
        print("   3. Restart computer when prompted")
        return False
    
    print("✅ WSL installation completed")
    print("⚠️ You may need to restart your computer")
    
    return True


def setup_wsl_vnc():
    """Set up VNC packages in WSL"""
    print("\n🔧 Setting up VNC packages in WSL...")
    
    commands = [
        ('sudo apt update -y', "Updating package list"),
        ('sudo apt install -y xvfb x11vnc', "Installing VNC packages"),
        ('pip3 install --user psutil', "Installing Python packages")
    ]
    
    for cmd, desc in commands:
        wsl_cmd = ['wsl', 'bash', '-c', cmd]
        success, output = run_command(wsl_cmd, desc, timeout=300)
        if not success:
            print(f"⚠️ Warning: {desc} failed")
            print("You may need to run this manually in WSL")
    
    # Verify installation
    success, _ = run_command(['wsl', 'bash', '-c', 'which xvfb-run && which x11vnc'], "Verifying VNC installation")
    if success:
        print("✅ VNC packages installed successfully in WSL")
        return True
    else:
        print("❌ VNC package verification failed")
        return False


def install_docker():
    """Guide user to install Docker"""
    print("\n🐳 Docker Installation Guide...")
    
    print("📋 To install Docker Desktop for Windows:")
    print("1. Go to: https://www.docker.com/products/docker-desktop")
    print("2. Download Docker Desktop for Windows")
    print("3. Run the installer")
    print("4. Restart your computer")
    print("5. Start Docker Desktop")
    
    print("\n💡 Alternative: Use Chocolatey package manager")
    print("   choco install docker-desktop")
    
    response = input("\nHave you installed Docker? (y/N): ").lower()
    return response == 'y'


def test_vnc_setup():
    """Test VNC setup"""
    print("\n🧪 Testing VNC setup...")
    
    # Test WSL VNC
    wsl_status = check_wsl_status()
    if wsl_status == "ready":
        print("✅ WSL VNC setup is ready")
        return True
    
    # Test Docker VNC
    docker_status = check_docker_status()
    if docker_status == "ready":
        print("✅ Docker VNC setup is ready")
        return True
    
    print("❌ No VNC setup is ready")
    return False


def main():
    """Main setup function"""
    print("🚀 Windows VNC Setup Assistant")
    print("=" * 50)
    
    if platform.system().lower() != "windows":
        print("❌ This script is for Windows only")
        return
    
    print("This script will help you set up VNC viewing for browser automation on Windows.")
    print("You can choose between WSL (Windows Subsystem for Linux) or Docker.")
    
    # Check current status
    wsl_status = check_wsl_status()
    docker_status = check_docker_status()
    
    print(f"\n📊 Current Status:")
    print(f"WSL: {wsl_status}")
    print(f"Docker: {docker_status}")
    
    # If already ready, no setup needed
    if wsl_status == "ready" or docker_status == "ready":
        print("\n🎉 VNC setup is already ready!")
        print("You can now use VNC mode in the browser automation interface.")
        return
    
    # Setup options
    print("\n🎯 Setup Options:")
    print("1. WSL + Ubuntu (Recommended)")
    print("2. Docker Desktop")
    print("3. Skip setup (use PC Browser mode only)")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == "1":
        # WSL setup path
        if wsl_status == "not_installed":
            if install_wsl():
                print("\n⚠️ Please restart your computer and run this script again")
                return
        elif wsl_status == "no_distro":
            print("\n📦 Installing Ubuntu distribution...")
            success, _ = run_command(['wsl', '--install', '-d', 'Ubuntu'], "Installing Ubuntu", timeout=600)
            if success:
                print("✅ Ubuntu installed")
            else:
                print("❌ Ubuntu installation failed")
                return
        
        if wsl_status == "needs_packages" or wsl_status == "no_distro":
            setup_wsl_vnc()
    
    elif choice == "2":
        # Docker setup path
        if docker_status == "not_installed":
            install_docker()
        elif docker_status == "not_running":
            print("\n🔧 Please start Docker Desktop and try again")
    
    elif choice == "3":
        print("\n✅ Setup skipped")
        print("You can use PC Browser mode for browser automation")
        return
    
    else:
        print("❌ Invalid choice")
        return
    
    # Test final setup
    print("\n" + "=" * 50)
    if test_vnc_setup():
        print("\n🎉 VNC setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the webUI: python webui.py")
        print("2. Go to '🤖 Agent Interactivo' tab")
        print("3. Select '📺 VNC Viewer (Remote)' mode")
        print("4. Submit a browser automation task")
        print("5. Click '🖥️ Open VNC Viewer' to watch in real-time")
    else:
        print("\n⚠️ VNC setup needs manual configuration")
        print("You can still use PC Browser mode for immediate functionality")
    
    print("\n✨ Setup complete!")


if __name__ == "__main__":
    main()
