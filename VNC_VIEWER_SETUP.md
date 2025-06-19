# 🖥️ VNC Viewer for Browser Automation - Setup Guide

## 🎯 Overview

The VNC Viewer feature allows you to watch browser automation tasks in real-time from within the web application. You can see exactly what the automation agent is doing as it navigates websites and performs tasks.

## ✨ Features

### **Real-time Browser Viewing**
- ✅ Watch browser automation as it happens
- ✅ See mouse movements, clicks, and navigation
- ✅ Monitor task progress visually
- ✅ Debug automation issues in real-time

### **Modal Window Interface**
- ✅ Resizable modal window with VNC viewer
- ✅ Window controls: minimize, maximize, close
- ✅ Move to background/foreground
- ✅ Doesn't interfere with main application

### **Task Queue Integration**
- ✅ Works with existing task queue system
- ✅ Optional feature - enable/disable as needed
- ✅ Maintains all current functionality
- ✅ Sequential task processing preserved

## 🔧 Installation

### **Step 1: Install VNC Dependencies**

Run the automated installer:

```bash
python install_vnc_dependencies.py
```

### **Step 2: Manual Installation (if needed)**

#### **Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y xvfb x11vnc
```

#### **Linux (CentOS/RHEL):**
```bash
sudo yum install -y xorg-x11-server-Xvfb x11vnc
```

#### **macOS:**
```bash
brew install x11vnc
```

#### **Windows:**
- Install TightVNC or RealVNC
- Or use WSL with Linux packages
- Or use Docker containers

### **Step 3: Verify Installation**

Test that VNC components are available:

```bash
# Check Xvfb
which Xvfb

# Check x11vnc
which x11vnc
```

## 🚀 Usage

### **Step 1: Enable VNC Viewer**

1. Open the webUI at http://localhost:7860
2. Go to "🤖 Agent Interactivo" tab
3. Find the "🖥️ Browser Automation Viewer" section
4. Check "Enable VNC Viewer"

### **Step 2: Submit a Task**

1. Enter a browser automation task:
   - `Navigate to google.com and search for "AI automation"`
   - `Go to wikipedia.org and find information about Python`
   - `Visit example.com and take a screenshot`

2. Click "▶️ Submit Task"

### **Step 3: Open VNC Viewer**

1. After the task starts, click "🖥️ Open VNC Viewer"
2. A modal window will open showing the browser automation
3. Watch the agent navigate and perform actions in real-time

### **Step 4: Control the Viewer**

- **Fullscreen**: Click "⛶ Fullscreen" button
- **Reconnect**: Click "🔄 Reconnect" if connection drops
- **Close**: Click "✕ Close" to close the viewer

## 🎮 VNC Viewer Controls

### **Toolbar Buttons**
- **⛶ Fullscreen**: Toggle fullscreen mode
- **🔄 Reconnect**: Reconnect to VNC server
- **✕ Close**: Close the VNC viewer modal

### **Connection Status**
- **🔌 Connecting**: Establishing connection
- **✅ Connected**: Successfully connected and viewing
- **🔌 Disconnected**: Connection lost or closed
- **❌ Error**: Connection failed

### **Keyboard Shortcuts**
- **F11**: Toggle fullscreen (when viewer is focused)
- **Escape**: Exit fullscreen mode

## 🔍 Troubleshooting

### **VNC Server Won't Start**

**Problem**: "Failed to start VNC server" error

**Solutions**:
1. Check if Xvfb and x11vnc are installed:
   ```bash
   which Xvfb
   which x11vnc
   ```

2. Check for port conflicts:
   ```bash
   netstat -an | grep 5999
   ```

3. Try different display number:
   - The system automatically finds free displays
   - Check `/tmp/.X*-lock` files

### **VNC Viewer Shows Black Screen**

**Problem**: VNC connects but shows black screen

**Solutions**:
1. Wait a few seconds for browser to start
2. Check if browser automation task is actually running
3. Try reconnecting with "🔄 Reconnect" button

### **Connection Refused Error**

**Problem**: "Connection refused" in VNC viewer

**Solutions**:
1. Ensure VNC server started successfully
2. Check firewall settings
3. Verify port 5999 is available
4. Restart the task to reinitialize VNC

### **Browser Not Visible**

**Problem**: VNC connects but browser window not visible

**Solutions**:
1. Check if browser is running in headless mode
2. Ensure VNC display environment is set correctly
3. Try submitting a new task

## ⚙️ Configuration

### **VNC Server Settings**

Default settings (automatically configured):
- **Display**: `:99` (auto-selected)
- **Port**: `5999` (auto-selected)
- **Resolution**: `1280x1024`
- **Color Depth**: `24-bit`

### **Browser Settings**

For VNC viewing to work:
- **Headless Mode**: Must be `False`
- **Display**: Automatically set to VNC display
- **Window Size**: Matches VNC resolution

### **Performance Settings**

For better performance:
- **VNC Quality**: Automatically optimized
- **Compression**: Enabled by default
- **Frame Rate**: Adaptive based on activity

## 🔒 Security Notes

### **Local Access Only**
- VNC server binds to localhost only
- No external network access
- No password required (local only)

### **Temporary Sessions**
- VNC server starts only when needed
- Automatically cleaned up after tasks
- No persistent VNC sessions

## 🎯 Use Cases

### **Development & Debugging**
- Watch automation scripts in action
- Debug element selection issues
- Monitor navigation problems
- Verify task completion

### **Demonstration**
- Show browser automation to others
- Create training materials
- Document automation workflows
- Present automation capabilities

### **Monitoring**
- Keep an eye on long-running tasks
- Ensure automation is progressing
- Catch unexpected behaviors
- Monitor resource usage

## 📋 Technical Details

### **Architecture**
```
WebUI → VNC Manager → Xvfb → x11vnc → noVNC Client
```

### **Components**
- **Xvfb**: Virtual framebuffer for headless display
- **x11vnc**: VNC server for X11 display
- **noVNC**: Web-based VNC client
- **VNC Manager**: Python wrapper for VNC lifecycle

### **Ports Used**
- **VNC Server**: 5999+ (auto-selected)
- **Display**: :99+ (auto-selected)
- **WebUI**: 7860 (existing)

## ✅ Status

**Current Implementation Status:**
- ✅ VNC server integration
- ✅ Web-based VNC client
- ✅ Modal window interface
- ✅ Task queue integration
- ✅ Automatic cleanup
- ✅ Error handling
- ✅ Cross-platform support

**Ready for Production Use!** 🚀

The VNC viewer feature is fully implemented and ready to provide real-time visual feedback for browser automation tasks.
