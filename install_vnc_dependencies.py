#!/usr/bin/env python3
"""
Install VNC dependencies for browser automation viewing
"""

import subprocess
import sys
import platform
import os


def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False


def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    dependencies = [
        "psutil",  # For process management
    ]
    
    for dep in dependencies:
        success = run_command(
            f"{sys.executable} -m pip install {dep}",
            f"Installing {dep}"
        )
        if not success:
            print(f"⚠️ Warning: Failed to install {dep}")


def install_linux_dependencies():
    """Install VNC dependencies on Linux"""
    print("\n🐧 Installing Linux VNC dependencies...")
    
    # Try different package managers
    package_managers = [
        {
            "name": "apt",
            "check": "which apt-get",
            "update": "sudo apt-get update",
            "install": "sudo apt-get install -y xvfb x11vnc"
        },
        {
            "name": "yum",
            "check": "which yum",
            "update": "sudo yum update -y",
            "install": "sudo yum install -y xorg-x11-server-Xvfb x11vnc"
        },
        {
            "name": "dnf",
            "check": "which dnf",
            "update": "sudo dnf update -y",
            "install": "sudo dnf install -y xorg-x11-server-Xvfb x11vnc"
        },
        {
            "name": "pacman",
            "check": "which pacman",
            "update": "sudo pacman -Sy",
            "install": "sudo pacman -S --noconfirm xorg-server-xvfb x11vnc"
        }
    ]
    
    for pm in package_managers:
        if run_command(pm["check"], f"Checking for {pm['name']}"):
            print(f"📦 Found {pm['name']} package manager")
            
            # Update package list
            run_command(pm["update"], f"Updating {pm['name']} package list")
            
            # Install VNC packages
            success = run_command(pm["install"], f"Installing VNC packages with {pm['name']}")
            
            if success:
                print(f"✅ Successfully installed VNC dependencies with {pm['name']}")
                return True
            else:
                print(f"❌ Failed to install with {pm['name']}")
    
    print("❌ Could not install VNC dependencies automatically")
    print("Please install manually:")
    print("  - Xvfb (X Virtual Framebuffer)")
    print("  - x11vnc (VNC server for X11)")
    return False


def install_macos_dependencies():
    """Install VNC dependencies on macOS"""
    print("\n🍎 Installing macOS VNC dependencies...")
    
    # Check for Homebrew
    if run_command("which brew", "Checking for Homebrew"):
        print("📦 Found Homebrew package manager")
        
        # Update Homebrew
        run_command("brew update", "Updating Homebrew")
        
        # Install VNC packages
        success = run_command(
            "brew install x11vnc",
            "Installing x11vnc with Homebrew"
        )
        
        if success:
            print("✅ Successfully installed VNC dependencies with Homebrew")
            print("ℹ️ Note: On macOS, you may need to enable Screen Sharing in System Preferences")
            return True
    
    print("❌ Homebrew not found. Please install Homebrew first:")
    print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    print("Then run this script again.")
    return False


def install_windows_dependencies():
    """Install VNC dependencies on Windows"""
    print("\n🪟 Windows VNC Setup...")
    
    print("ℹ️ On Windows, VNC functionality requires additional setup:")
    print("1. Install a VNC server like TightVNC or RealVNC")
    print("2. Or use Windows Subsystem for Linux (WSL) with Linux VNC packages")
    print("3. Alternatively, use Docker with Linux containers")
    
    print("\n📋 Recommended options:")
    print("Option 1 - TightVNC:")
    print("  Download from: https://www.tightvnc.com/download.php")
    
    print("\nOption 2 - WSL with Ubuntu:")
    print("  1. Install WSL: wsl --install")
    print("  2. Install Ubuntu from Microsoft Store")
    print("  3. Run this script inside WSL")
    
    print("\nOption 3 - Docker:")
    print("  Use a Docker container with VNC support")
    
    return False


def test_vnc_installation():
    """Test if VNC components are properly installed"""
    print("\n🧪 Testing VNC installation...")
    
    tests = [
        ("Xvfb", "which Xvfb"),
        ("x11vnc", "which x11vnc"),
    ]
    
    all_passed = True
    
    for name, command in tests:
        if run_command(command, f"Testing {name}"):
            print(f"✅ {name} is available")
        else:
            print(f"❌ {name} is not available")
            all_passed = False
    
    return all_passed


def main():
    """Main installation function"""
    print("🚀 VNC Dependencies Installer for Browser Automation")
    print("=" * 60)
    
    # Install Python dependencies first
    install_python_dependencies()
    
    # Detect operating system and install accordingly
    system = platform.system().lower()
    
    if system == "linux":
        success = install_linux_dependencies()
    elif system == "darwin":  # macOS
        success = install_macos_dependencies()
    elif system == "windows":
        success = install_windows_dependencies()
    else:
        print(f"❌ Unsupported operating system: {system}")
        success = False
    
    # Test installation
    if success and system != "windows":
        print("\n" + "=" * 60)
        if test_vnc_installation():
            print("\n🎉 VNC dependencies installed successfully!")
            print("You can now use the VNC viewer feature in the browser automation.")
        else:
            print("\n⚠️ Some VNC components may not be working properly.")
            print("Please check the installation manually.")
    
    print("\n📋 Next steps:")
    print("1. Restart the webUI application")
    print("2. Go to the '🤖 Agent Interactivo' tab")
    print("3. Enable 'VNC Viewer' option")
    print("4. Submit a browser automation task")
    print("5. Click 'Open VNC Viewer' to watch the automation")
    
    print("\n✨ Happy automating!")


if __name__ == "__main__":
    main()
