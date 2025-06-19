#!/usr/bin/env python3
"""
Simplified VNC Server for Windows - Testing and Mobile Access
"""

import asyncio
import logging
import os
import subprocess
import sys
import socket
import platform
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SimpleVNCServer:
    """Simplified VNC server for Windows testing"""
    
    def __init__(self, display_number: int = 99, port: int = 5999):
        self.display_number = display_number
        self.port = port
        self.display_name = f":{display_number}"
        self.is_running = False
        self.screen_width = 1280
        self.screen_height = 1024
        self.method_used = None
        self.vnc_process = None
        
    def _find_free_port(self, start_port: int = 5900) -> int:
        """Find a free port for VNC server"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))  # Bind to all interfaces for mobile access
                    return port
            except OSError:
                continue
        raise RuntimeError("No free ports available for VNC server")
    
    def _check_wsl_simple(self) -> bool:
        """Simple WSL check"""
        try:
            result = subprocess.run(['wsl', '--list'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and ('Ubuntu' in result.stdout or 'Debian' in result.stdout)
        except Exception:
            return False
    
    async def _start_mock_vnc(self) -> Dict[str, Any]:
        """Start a mock VNC server for testing (Windows fallback)"""
        try:
            logger.info("Starting mock VNC server for Windows testing...")
            
            # Find free port
            self.port = self._find_free_port()
            
            # Create a simple HTTP server that serves the VNC viewer
            # This is a fallback for Windows when WSL/Docker aren't available
            mock_vnc_script = f"""
import http.server
import socketserver
import threading
import time

class MockVNCHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>AUTONOBOT</title>
                <meta charset="UTF-8">
                <style>
                    body {{
                        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
                        color: #00ffff;
                        font-family: 'Courier New', monospace;
                        padding: 20px;
                        margin: 0;
                        min-height: 100vh;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        border: 2px solid #00ffff;
                        border-radius: 12px;
                        padding: 30px;
                        box-shadow: 0 0 20px #00ffff;
                    }}
                    h1 {{
                        color: #00ffff;
                        text-align: center;
                        text-shadow: 0 0 10px #00ffff;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                        font-weight: 900;
                        letter-spacing: 3px;
                        text-transform: uppercase;
                    }}
                    h2 {{
                        color: #00ff41;
                        text-align: center;
                        text-shadow: 0 0 8px #00ff41;
                        font-size: 1.2rem;
                        margin-bottom: 30px;
                        font-weight: 600;
                        letter-spacing: 2px;
                        text-transform: uppercase;
                    }}
                    .status-panel {{
                        border: 1px solid #00ff41;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                        background: rgba(0, 255, 65, 0.1);
                    }}
                    .status-item {{
                        margin: 10px 0;
                        font-size: 1.1rem;
                    }}
                    .pulse {{
                        animation: pulse 2s ease-in-out infinite alternate;
                    }}
                    @keyframes pulse {{
                        0% {{ opacity: 0.7; }}
                        100% {{ opacity: 1; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 AUTONOBOT</h1>
                    <h2>Navegador Autonomo Avanzado</h2>
                    <div class="status-panel">
                        <h3>Sistema de Navegacion Autonoma</h3>
                        <div class="status-item">✅ VNC Server: Running on port {self.port}</div>
                        <div class="status-item">✅ Display: Virtual display {self.display_name}</div>
                        <div class="status-item">✅ Resolution: {self.screen_width}x{self.screen_height}</div>
                        <div class="status-item pulse">🔄 Status: Ready for browser automation</div>
                    </div>
                    <p style="text-align: center; margin-top: 30px;">
                        This is a test VNC server for Windows.<br>
                        For full VNC functionality, please set up WSL or Docker.
                    </p>
                </div>
                <script>
                    // Simulate VNC activity with cyberpunk effects
                    setInterval(() => {{
                        const panel = document.querySelector('.status-panel');
                        panel.style.backgroundColor = panel.style.backgroundColor === 'rgba(0,255,65,0.2)' ? 'rgba(0,255,65,0.1)' : 'rgba(0,255,65,0.2)';
                    }}, 2000);
                </script>
            </body>
            </html>
            '''
            self.wfile.write(html.encode())
        else:
            super().do_GET()

PORT = {self.port}
Handler = MockVNCHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Mock VNC server running on port {{PORT}}")
    httpd.serve_forever()
"""
            
            # Write and execute mock server with proper encoding
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(mock_vnc_script)
                script_path = f.name
            
            # Start mock VNC server
            self.vnc_process = subprocess.Popen([sys.executable, script_path], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test if server is responding
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    result = s.connect_ex(('localhost', self.port))
                    if result == 0:
                        self.is_running = True
                        self.method_used = "Mock"
                        logger.info(f"Mock VNC server started on port {self.port}")
                        
                        return {
                            "status": "success",
                            "method": "Mock",
                            "display": self.display_name,
                            "port": self.port,
                            "width": self.screen_width,
                            "height": self.screen_height,
                            "vnc_url": f"localhost:{self.port}",
                            "note": "Mock VNC server for testing. Set up WSL or Docker for full functionality."
                        }
            except Exception as e:
                logger.warning(f"Mock VNC connection test failed: {e}")
            
            return {
                "status": "error",
                "error": "Mock VNC server failed to start"
            }
            
        except Exception as e:
            logger.error(f"Mock VNC startup failed: {e}")
            return {
                "status": "error",
                "error": f"Mock VNC startup failed: {str(e)}"
            }
    
    async def _start_wsl_vnc_simple(self) -> Dict[str, Any]:
        """Start VNC using WSL (simplified)"""
        try:
            logger.info("Starting VNC server using WSL...")
            
            # Find free port
            self.port = self._find_free_port()
            
            # Simple WSL VNC command
            wsl_cmd = f"""
export DISPLAY=:{self.display_number}
pkill -f "Xvfb.*:{self.display_number}" 2>/dev/null || true
pkill -f "x11vnc.*:{self.display_number}" 2>/dev/null || true
Xvfb :{self.display_number} -screen 0 {self.screen_width}x{self.screen_height}x24 -ac &
sleep 2
x11vnc -display :{self.display_number} -rfbport {self.port} -forever -shared -nopw -quiet &
echo "VNC server started on port {self.port}"
"""
            
            # Execute in WSL
            self.vnc_process = subprocess.Popen(
                ['wsl', 'bash', '-c', wsl_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for VNC to start
            await asyncio.sleep(5)
            
            # Test connection
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    result = s.connect_ex(('localhost', self.port))
                    if result == 0:
                        self.is_running = True
                        self.method_used = "WSL"
                        logger.info(f"WSL VNC server started on port {self.port}")
                        
                        return {
                            "status": "success",
                            "method": "WSL",
                            "display": self.display_name,
                            "port": self.port,
                            "width": self.screen_width,
                            "height": self.screen_height,
                            "vnc_url": f"localhost:{self.port}"
                        }
            except Exception as e:
                logger.warning(f"WSL VNC connection test failed: {e}")
            
            return {
                "status": "error",
                "error": "WSL VNC server failed to start properly"
            }
            
        except Exception as e:
            logger.error(f"WSL VNC startup failed: {e}")
            return {
                "status": "error",
                "error": f"WSL VNC startup failed: {str(e)}"
            }
    
    async def start_server(self) -> Dict[str, Any]:
        """Start VNC server using the best available method"""
        try:
            logger.info("Starting simplified VNC server for Windows...")
            
            # Method 1: Try WSL if available
            if self._check_wsl_simple():
                logger.info("WSL detected, attempting WSL VNC...")
                result = await self._start_wsl_vnc_simple()
                if result.get("status") == "success":
                    return result
                logger.warning("WSL VNC failed, falling back to mock server")
            
            # Method 2: Fallback to mock VNC server for testing
            logger.info("Starting mock VNC server for testing...")
            return await self._start_mock_vnc()
            
        except Exception as e:
            logger.error(f"VNC server startup failed: {e}")
            return {
                "status": "error",
                "error": f"VNC server startup failed: {str(e)}"
            }
    
    async def stop_server(self):
        """Stop VNC server"""
        try:
            logger.info(f"Stopping VNC server (method: {self.method_used})")
            
            if self.vnc_process:
                self.vnc_process.terminate()
                try:
                    self.vnc_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.vnc_process.kill()
                self.vnc_process = None
            
            if self.method_used == "WSL":
                # Stop WSL processes
                try:
                    subprocess.run(['wsl', 'pkill', '-f', f'x11vnc.*:{self.display_number}'], timeout=5)
                    subprocess.run(['wsl', 'pkill', '-f', f'Xvfb.*:{self.display_number}'], timeout=5)
                except Exception as e:
                    logger.warning(f"Error stopping WSL VNC: {e}")
            
            self.is_running = False
            self.method_used = None
            logger.info("VNC server stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping VNC server: {e}")
    
    def get_display_env(self) -> Dict[str, str]:
        """Get environment variables for running applications on this display"""
        if self.method_used == "WSL":
            return {
                "DISPLAY": self.display_name,
                "XAUTHORITY": f"/tmp/.X{self.display_number}-auth"
            }
        else:
            # For mock server, return empty env (browser will run normally)
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current VNC server status"""
        return {
            "is_running": self.is_running,
            "method": self.method_used,
            "display": self.display_name if self.is_running else None,
            "port": self.port if self.is_running else None,
            "width": self.screen_width,
            "height": self.screen_height,
            "vnc_url": f"localhost:{self.port}" if self.is_running else None
        }
