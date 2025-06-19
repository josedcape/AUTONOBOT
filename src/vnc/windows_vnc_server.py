#!/usr/bin/env python3
"""
Windows-compatible VNC Server implementation using multiple approaches
"""

import asyncio
import logging
import os
import subprocess
import platform
import socket
import time
from typing import Optional, Dict, Any
import tempfile
import shutil

logger = logging.getLogger(__name__)


class WindowsVNCServer:
    """Windows-compatible VNC server using multiple fallback approaches"""
    
    def __init__(self, display_number: int = 99, port: int = 5999):
        self.display_number = display_number
        self.port = port
        self.display_name = f":{display_number}"
        self.vnc_process: Optional[subprocess.Popen] = None
        self.xvfb_process: Optional[subprocess.Popen] = None
        self.wsl_process: Optional[subprocess.Popen] = None
        self.docker_container: Optional[str] = None
        self.is_running = False
        self.screen_width = 1280
        self.screen_height = 1024
        self.method_used = None
        
    def _find_free_port(self, start_port: int = 5900) -> int:
        """Find a free port for VNC server"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No free ports available for VNC server")
    
    def _check_wsl_available(self) -> bool:
        """Check if WSL is available and has required packages"""
        try:
            # Check if WSL is installed
            result = subprocess.run(['wsl', '--list'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # Check if Ubuntu or similar distribution is available
            if 'Ubuntu' not in result.stdout and 'Debian' not in result.stdout:
                return False
            
            # Check if required packages are installed in WSL
            check_cmd = ['wsl', 'bash', '-c', 'which xvfb-run && which x11vnc']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"WSL check failed: {e}")
            return False
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Docker check failed: {e}")
            return False
    
    def _setup_wsl_vnc(self) -> bool:
        """Setup VNC packages in WSL if not already installed"""
        try:
            logger.info("Setting up VNC packages in WSL...")
            
            # Update package list and install VNC packages
            setup_commands = [
                'sudo apt update -y',
                'sudo apt install -y xvfb x11vnc python3-pip',
                'pip3 install --user psutil'
            ]
            
            for cmd in setup_commands:
                wsl_cmd = ['wsl', 'bash', '-c', cmd]
                result = subprocess.run(wsl_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    logger.warning(f"WSL setup command failed: {cmd}")
                    logger.warning(f"Error: {result.stderr}")
            
            # Verify installation
            return self._check_wsl_available()
            
        except Exception as e:
            logger.error(f"WSL setup failed: {e}")
            return False
    
    async def _start_wsl_vnc(self) -> Dict[str, Any]:
        """Start VNC server using WSL"""
        try:
            logger.info("Starting VNC server using WSL...")
            
            # Find free port
            self.port = self._find_free_port()
            
            # Create WSL VNC startup script
            vnc_script = f"""#!/bin/bash
export DISPLAY=:{self.display_number}
export XAUTHORITY=/tmp/.X{self.display_number}-auth

# Kill any existing processes
pkill -f "Xvfb.*:{self.display_number}" || true
pkill -f "x11vnc.*:{self.display_number}" || true

# Start Xvfb
Xvfb :{self.display_number} -screen 0 {self.screen_width}x{self.screen_height}x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 3

# Start x11vnc
x11vnc -display :{self.display_number} -rfbport {self.port} -forever -shared -nopw -quiet -bg

echo "VNC server started on port {self.port}"
echo "XVFB_PID=$XVFB_PID"
"""
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(vnc_script)
                script_path = f.name
            
            try:
                # Copy script to WSL and make executable
                wsl_script_path = f"/tmp/vnc_start_{self.port}.sh"
                subprocess.run(['wsl', 'cp', script_path, wsl_script_path], check=True)
                subprocess.run(['wsl', 'chmod', '+x', wsl_script_path], check=True)
                
                # Execute script in WSL
                self.wsl_process = subprocess.Popen(
                    ['wsl', 'bash', wsl_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for VNC to start
                await asyncio.sleep(5)
                
                # Check if VNC is running by trying to connect
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2)
                        result = s.connect_ex(('localhost', self.port))
                        if result == 0:
                            self.is_running = True
                            self.method_used = "WSL"
                            logger.info(f"WSL VNC server started successfully on port {self.port}")
                            
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
                    logger.warning(f"VNC connection test failed: {e}")
                
                return {
                    "status": "error",
                    "error": "WSL VNC server failed to start properly"
                }
                
            finally:
                # Clean up temporary script
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"WSL VNC startup failed: {e}")
            return {
                "status": "error",
                "error": f"WSL VNC startup failed: {str(e)}"
            }
    
    async def _start_docker_vnc(self) -> Dict[str, Any]:
        """Start VNC server using Docker"""
        try:
            logger.info("Starting VNC server using Docker...")
            
            # Find free port
            self.port = self._find_free_port()
            
            # Create Dockerfile content
            dockerfile_content = f"""
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:{self.display_number}

RUN apt-get update && apt-get install -y \\
    xvfb \\
    x11vnc \\
    chromium-browser \\
    python3 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

EXPOSE {self.port}

CMD Xvfb :{self.display_number} -screen 0 {self.screen_width}x{self.screen_height}x24 -ac +extension GLX +render -noreset & \\
    sleep 3 && \\
    x11vnc -display :{self.display_number} -rfbport {self.port} -forever -shared -nopw -quiet
"""
            
            # Create temporary directory for Docker build
            with tempfile.TemporaryDirectory() as temp_dir:
                dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                # Build Docker image
                image_name = f"vnc-server-{self.port}"
                build_cmd = ['docker', 'build', '-t', image_name, temp_dir]
                result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    return {
                        "status": "error",
                        "error": f"Docker build failed: {result.stderr}"
                    }
                
                # Run Docker container
                container_name = f"vnc-container-{self.port}"
                run_cmd = [
                    'docker', 'run', '-d',
                    '--name', container_name,
                    '-p', f'{self.port}:{self.port}',
                    image_name
                ]
                
                result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    return {
                        "status": "error",
                        "error": f"Docker run failed: {result.stderr}"
                    }
                
                self.docker_container = container_name
                
                # Wait for container to start
                await asyncio.sleep(10)
                
                # Check if VNC is accessible
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5)
                        result = s.connect_ex(('localhost', self.port))
                        if result == 0:
                            self.is_running = True
                            self.method_used = "Docker"
                            logger.info(f"Docker VNC server started successfully on port {self.port}")
                            
                            return {
                                "status": "success",
                                "method": "Docker",
                                "display": self.display_name,
                                "port": self.port,
                                "width": self.screen_width,
                                "height": self.screen_height,
                                "vnc_url": f"localhost:{self.port}"
                            }
                except Exception as e:
                    logger.warning(f"Docker VNC connection test failed: {e}")
                
                return {
                    "status": "error",
                    "error": "Docker VNC server failed to start properly"
                }
                
        except Exception as e:
            logger.error(f"Docker VNC startup failed: {e}")
            return {
                "status": "error",
                "error": f"Docker VNC startup failed: {str(e)}"
            }
    
    async def start_server(self) -> Dict[str, Any]:
        """Start VNC server using the best available method on Windows"""
        try:
            logger.info("Starting Windows-compatible VNC server...")
            
            # Method 1: Try WSL if available
            if self._check_wsl_available():
                logger.info("WSL with VNC packages detected, using WSL method")
                result = await self._start_wsl_vnc()
                if result.get("status") == "success":
                    return result
                logger.warning("WSL VNC failed, trying next method")
            
            # Method 2: Try to setup WSL if it exists but lacks packages
            elif platform.system().lower() == "windows":
                try:
                    # Check if WSL exists but needs setup
                    wsl_check = subprocess.run(['wsl', '--list'], capture_output=True, text=True, timeout=5)
                    if wsl_check.returncode == 0 and ('Ubuntu' in wsl_check.stdout or 'Debian' in wsl_check.stdout):
                        logger.info("WSL detected but VNC packages missing, attempting setup...")
                        if self._setup_wsl_vnc():
                            result = await self._start_wsl_vnc()
                            if result.get("status") == "success":
                                return result
                except Exception as e:
                    logger.debug(f"WSL setup attempt failed: {e}")
            
            # Method 3: Try Docker if available
            if self._check_docker_available():
                logger.info("Docker detected, using Docker method")
                result = await self._start_docker_vnc()
                if result.get("status") == "success":
                    return result
                logger.warning("Docker VNC failed")
            
            # If all methods fail, return helpful error message
            return {
                "status": "error",
                "error": "VNC server requires WSL with Ubuntu/Debian or Docker. Please install one of these options.",
                "suggestions": [
                    "Install WSL: Run 'wsl --install' in PowerShell as Administrator",
                    "Install Docker Desktop for Windows",
                    "Use PC Browser mode for immediate functionality"
                ]
            }
            
        except Exception as e:
            logger.error(f"Windows VNC server startup failed: {e}")
            return {
                "status": "error",
                "error": f"VNC server startup failed: {str(e)}"
            }
    
    async def stop_server(self):
        """Stop VNC server"""
        try:
            logger.info(f"Stopping VNC server (method: {self.method_used})")
            
            if self.method_used == "WSL" and self.wsl_process:
                # Stop WSL processes
                try:
                    subprocess.run(['wsl', 'pkill', '-f', f'x11vnc.*:{self.display_number}'], timeout=10)
                    subprocess.run(['wsl', 'pkill', '-f', f'Xvfb.*:{self.display_number}'], timeout=10)
                    self.wsl_process.terminate()
                except Exception as e:
                    logger.warning(f"Error stopping WSL VNC: {e}")
                self.wsl_process = None
            
            elif self.method_used == "Docker" and self.docker_container:
                # Stop Docker container
                try:
                    subprocess.run(['docker', 'stop', self.docker_container], timeout=30)
                    subprocess.run(['docker', 'rm', self.docker_container], timeout=30)
                except Exception as e:
                    logger.warning(f"Error stopping Docker VNC: {e}")
                self.docker_container = None
            
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
        elif self.method_used == "Docker":
            return {
                "DISPLAY": self.display_name
            }
        else:
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
