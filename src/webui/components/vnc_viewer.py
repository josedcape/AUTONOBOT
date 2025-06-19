#!/usr/bin/env python3
"""
VNC Viewer component for browser automation
"""

import gradio as gr
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def create_vnc_viewer_modal():
    """Create VNC viewer modal window"""
    
    # VNC viewer HTML template with noVNC
    vnc_viewer_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Browser Automation VNC Viewer</title>
        <meta charset="utf-8">
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #1a1a1a;
                font-family: Arial, sans-serif;
            }
            
            /* Cyberpunk VNC Viewer Styling */
            :root {
                --cyber-primary: #00ffff;
                --cyber-secondary: #ff00ff;
                --cyber-accent: #00ff41;
                --cyber-purple: #7b2cbf;
                --cyber-dark: #0a0a0a;
                --cyber-dark-secondary: #1a1a2e;
                --cyber-dark-tertiary: #16213e;
                --cyber-text: #ffffff;
                --cyber-text-dim: #cccccc;
                --cyber-glow: 0 0 10px;
            }

            .vnc-container {
                width: 100%;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: linear-gradient(135deg, var(--cyber-dark) 0%, var(--cyber-dark-secondary) 100%);
                border: 2px solid var(--cyber-primary);
                box-shadow: var(--cyber-glow) var(--cyber-primary);
                /* Mobile-friendly styles */
                touch-action: manipulation;
                -webkit-overflow-scrolling: touch;
                position: relative;
                font-family: 'Rajdhani', 'Segoe UI', sans-serif;
            }

            .vnc-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, transparent 30%, rgba(0, 255, 255, 0.1) 50%, transparent 70%);
                animation: cyber-scan 3s linear infinite;
                pointer-events: none;
                z-index: 1;
            }

            @keyframes cyber-scan {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }

            .vnc-toolbar {
                background: linear-gradient(45deg, var(--cyber-dark-tertiary), var(--cyber-dark-secondary));
                padding: 15px;
                border-bottom: 2px solid var(--cyber-primary);
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                z-index: 2;
            }

            .vnc-title {
                color: var(--cyber-text);
                font-weight: 700;
                margin: 0;
                font-size: 18px;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: var(--cyber-glow) var(--cyber-primary);
                font-family: 'Orbitron', monospace;
            }

            .vnc-controls {
                display: flex;
                gap: 12px;
            }

            .vnc-btn {
                background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary));
                color: var(--cyber-dark);
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: all 0.3s ease;
                box-shadow: var(--cyber-glow) var(--cyber-primary);
                font-family: 'Rajdhani', sans-serif;
            }

            .vnc-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 0 20px var(--cyber-primary);
                background: linear-gradient(45deg, var(--cyber-secondary), var(--cyber-accent));
            }

            .vnc-btn.close {
                background: linear-gradient(45deg, #ff0040, #ff4081);
                box-shadow: var(--cyber-glow) #ff0040;
            }

            .vnc-btn.close:hover {
                background: linear-gradient(45deg, #ff4081, #ff6b9d);
                box-shadow: 0 0 20px #ff0040;
            }

            .vnc-viewer {
                flex: 1;
                background: var(--cyber-dark);
                position: relative;
                overflow: hidden;
                z-index: 2;
            }

            .vnc-status {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: var(--cyber-text);
                text-align: center;
                z-index: 10;
                font-family: 'Orbitron', monospace;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 2px;
            }

            .vnc-loading {
                color: var(--cyber-accent);
                text-shadow: var(--cyber-glow) var(--cyber-accent);
                animation: pulse-glow 2s ease-in-out infinite alternate;
            }

            .vnc-error {
                color: #ff0040;
                text-shadow: var(--cyber-glow) #ff0040;
                animation: pulse-glow 1s ease-in-out infinite alternate;
            }

            .vnc-disconnected {
                color: #ffaa00;
                text-shadow: var(--cyber-glow) #ffaa00;
                animation: pulse-glow 1.5s ease-in-out infinite alternate;
            }

            @keyframes pulse-glow {
                0% {
                    opacity: 0.7;
                    transform: translate(-50%, -50%) scale(1);
                }
                100% {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1.05);
                }
            }

            #vnc-canvas {
                width: 100%;
                height: 100%;
                object-fit: contain;
                border: 1px solid var(--cyber-primary);
                border-radius: 4px;
            }

            /* Mobile VNC Optimizations */
            .vnc-mobile-controls {
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                display: none;
                background: rgba(26, 26, 46, 0.9);
                border: 1px solid var(--cyber-primary);
                border-radius: 25px;
                padding: 8px 16px;
                z-index: 100;
            }

            .vnc-mobile-btn {
                background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary));
                border: none;
                color: var(--cyber-dark);
                padding: 8px 12px;
                margin: 0 4px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                min-width: 44px;
                min-height: 44px;
            }

            .vnc-mobile-btn:active {
                transform: scale(0.95);
                background: linear-gradient(45deg, var(--cyber-secondary), var(--cyber-accent));
            }

            /* Touch gestures indicator */
            .vnc-touch-hint {
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0, 255, 255, 0.1);
                border: 1px solid var(--cyber-primary);
                border-radius: 8px;
                padding: 8px 12px;
                color: var(--cyber-text);
                font-size: 12px;
                z-index: 100;
                display: none;
            }

            /* Mobile responsive adjustments */
            @media (max-width: 768px) {
                .vnc-container {
                    height: 100vh;
                    border-radius: 0;
                }

                .vnc-toolbar {
                    padding: 12px;
                    flex-wrap: wrap;
                }

                .vnc-title {
                    font-size: 16px;
                    margin-bottom: 8px;
                    width: 100%;
                    text-align: center;
                }

                .vnc-controls {
                    width: 100%;
                    justify-content: center;
                    gap: 8px;
                }

                .vnc-btn {
                    padding: 10px 14px;
                    font-size: 11px;
                    min-width: 44px;
                    min-height: 44px;
                }

                .vnc-mobile-controls {
                    display: flex;
                }

                .vnc-touch-hint {
                    display: block;
                }
            }

            /* Touch device specific */
            @media (hover: none) and (pointer: coarse) {
                .vnc-mobile-controls {
                    display: flex !important;
                }

                .vnc-touch-hint {
                    display: block !important;
                }

                .vnc-btn:hover {
                    transform: none;
                }

                .vnc-btn:active {
                    transform: scale(0.95);
                }
            }

            /* Mobile responsive styles */
            @media (max-width: 768px) {
                .vnc-toolbar {
                    padding: 5px;
                    flex-wrap: wrap;
                }

                .vnc-btn {
                    padding: 8px 12px;
                    font-size: 14px;
                    margin: 2px;
                }

                .vnc-title {
                    font-size: 14px;
                }

                .vnc-container {
                    height: 100vh;
                }
            }

            /* Touch-friendly controls */
            @media (pointer: coarse) {
                .vnc-btn {
                    min-height: 44px;
                    min-width: 44px;
                }
            }
        </style>
        
        <!-- noVNC CSS and JS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/novnc@1.4.0/app/styles/base.css">
        <script src="https://cdn.jsdelivr.net/npm/novnc@1.4.0/core/rfb.js"></script>
    </head>
    <body>
        <div class="vnc-container">
            <div class="vnc-toolbar">
                <h3 class="vnc-title">🤖 AUTONOBOT</h3>
                <div class="vnc-controls">
                    <button class="vnc-btn" onclick="toggleFullscreen()">⛶ Pantalla Completa</button>
                    <button class="vnc-btn" onclick="reconnectVNC()">🔄 Reconectar</button>
                    <button class="vnc-btn close" onclick="closeViewer()">✕ Cerrar</button>
                </div>
            </div>

            <div class="vnc-viewer">
                <div class="vnc-touch-hint">
                    📱 Toca y arrastra para navegar • Pellizca para zoom
                </div>

                <div id="vnc-status" class="vnc-status vnc-loading">
                    <div>🔌 Conectando al sistema de navegacion autonoma...</div>
                    <div style="font-size: 12px; margin-top: 10px;">Estableciendo conexion con el agente inteligente</div>
                </div>

                <div id="vnc-screen" style="width: 100%; height: 100%; display: none;"></div>

                <div class="vnc-mobile-controls">
                    <button class="vnc-mobile-btn" onclick="vncZoomIn()" title="Zoom In">🔍+</button>
                    <button class="vnc-mobile-btn" onclick="vncZoomOut()" title="Zoom Out">🔍-</button>
                    <button class="vnc-mobile-btn" onclick="vncCenter()" title="Centrar">🎯</button>
                    <button class="vnc-mobile-btn" onclick="vncKeyboard()" title="Teclado">⌨️</button>
                </div>
            </div>
        </div>
        
        <script>
            let rfb = null;
            let vncHost = 'localhost';
            let vncPort = 5999;
            let isConnected = false;
            
            // Initialize VNC connection
            function initVNC(host, port) {
                vncHost = host || 'localhost';
                vncPort = port || 5999;

                // Try different connection methods for better compatibility
                const protocols = ['ws:', 'wss:'];
                const hosts = [vncHost, window.location.hostname];

                let vncUrl = `ws://${vncHost}:${vncPort}`;

                // For mobile devices, try to use the current host
                if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    vncUrl = `ws://${window.location.hostname}:${vncPort}`;
                }

                console.log('Connecting to VNC:', vncUrl);

                try {
                    rfb = new RFB(document.getElementById('vnc-screen'), vncUrl);

                    rfb.addEventListener('connect', onVNCConnect);
                    rfb.addEventListener('disconnect', onVNCDisconnect);
                    rfb.addEventListener('credentialsrequired', onVNCCredentials);

                    // Configure RFB settings for mobile compatibility
                    rfb.scaleViewport = true;
                    rfb.resizeSession = false;
                    rfb.viewOnly = false;
                    rfb.focusOnClick = true;

                    // Mobile-specific settings
                    if (window.innerWidth <= 768) {
                        rfb.touchButton = 1; // Enable touch support
                    }

                } catch (error) {
                    console.error('VNC connection error:', error);
                    showStatus('❌ Connection failed: ' + error.message + ' (Try: python setup_windows_vnc.py)', 'vnc-error');
                }
            }
            
            function onVNCConnect() {
                console.log('VNC connected');
                isConnected = true;
                document.getElementById('vnc-status').style.display = 'none';
                document.getElementById('vnc-screen').style.display = 'block';
            }
            
            function onVNCDisconnect() {
                console.log('VNC disconnected');
                isConnected = false;
                document.getElementById('vnc-status').style.display = 'block';
                document.getElementById('vnc-screen').style.display = 'none';
                showStatus('🔌 Disconnected from browser automation', 'vnc-disconnected');
            }
            
            function onVNCCredentials() {
                console.log('VNC credentials required');
                // For now, we use no password setup
            }
            
            function showStatus(message, className) {
                const statusEl = document.getElementById('vnc-status');
                statusEl.innerHTML = `<div>${message}</div>`;
                statusEl.className = 'vnc-status ' + className;
            }
            
            function reconnectVNC() {
                if (rfb) {
                    rfb.disconnect();
                }
                showStatus('🔄 Reconnecting...', 'vnc-loading');
                setTimeout(() => initVNC(vncHost, vncPort), 1000);
            }
            
            function toggleFullscreen() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            }
            
            function closeViewer() {
                if (rfb) {
                    rfb.disconnect();
                }
                // Send message to parent window to close modal
                if (window.parent) {
                    window.parent.postMessage({type: 'close-vnc-viewer'}, '*');
                }
            }
            
            // Listen for VNC connection info from parent
            window.addEventListener('message', function(event) {
                if (event.data.type === 'vnc-connect') {
                    const {host, port} = event.data;
                    initVNC(host, port);
                }
            });
            
            // Auto-connect on load (with default values)
            window.addEventListener('load', function() {
                // Wait a bit for any parent messages
                setTimeout(() => {
                    if (!isConnected) {
                        initVNC();
                    }
                }, 1000);

                // Initialize mobile optimizations
                initMobileControls();
            });

            // Mobile VNC Controls
            let vncScale = 1;
            let vncOffsetX = 0;
            let vncOffsetY = 0;

            function vncZoomIn() {
                vncScale = Math.min(vncScale * 1.2, 3);
                applyVncTransform();
            }

            function vncZoomOut() {
                vncScale = Math.max(vncScale / 1.2, 0.5);
                applyVncTransform();
            }

            function vncCenter() {
                vncOffsetX = 0;
                vncOffsetY = 0;
                vncScale = 1;
                applyVncTransform();
            }

            function vncKeyboard() {
                // Toggle virtual keyboard for mobile
                const input = document.createElement('input');
                input.style.position = 'absolute';
                input.style.left = '-9999px';
                input.style.opacity = '0';
                document.body.appendChild(input);
                input.focus();
                setTimeout(() => document.body.removeChild(input), 100);
            }

            function applyVncTransform() {
                const screen = document.getElementById('vnc-screen');
                if (screen) {
                    screen.style.transform = `scale(${vncScale}) translate(${vncOffsetX}px, ${vncOffsetY}px)`;
                    screen.style.transformOrigin = 'center center';
                }
            }

            function initMobileControls() {
                // Add touch-friendly class for mobile devices
                if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
                    document.body.classList.add('touch-device');
                }

                // Auto-hide mobile controls after inactivity
                let hideControlsTimeout;
                const mobileControls = document.querySelector('.vnc-mobile-controls');

                function showMobileControls() {
                    if (mobileControls) {
                        mobileControls.style.opacity = '1';
                        clearTimeout(hideControlsTimeout);
                        hideControlsTimeout = setTimeout(() => {
                            mobileControls.style.opacity = '0.7';
                        }, 3000);
                    }
                }

                document.addEventListener('touchstart', showMobileControls);
                document.addEventListener('mousemove', showMobileControls);

                // Touch gesture handling for VNC
                let touchStartX = 0;
                let touchStartY = 0;
                let touchStartDistance = 0;
                let touchStartScale = 1;

                document.addEventListener('touchstart', function(e) {
                    const vncViewer = document.querySelector('.vnc-viewer');
                    if (!vncViewer || !vncViewer.contains(e.target)) return;

                    if (e.touches.length === 1) {
                        touchStartX = e.touches[0].clientX;
                        touchStartY = e.touches[0].clientY;
                    } else if (e.touches.length === 2) {
                        const dx = e.touches[0].clientX - e.touches[1].clientX;
                        const dy = e.touches[0].clientY - e.touches[1].clientY;
                        touchStartDistance = Math.sqrt(dx * dx + dy * dy);
                        touchStartScale = vncScale;
                    }
                    e.preventDefault();
                });

                document.addEventListener('touchmove', function(e) {
                    const vncViewer = document.querySelector('.vnc-viewer');
                    if (!vncViewer || !vncViewer.contains(e.target)) return;

                    if (e.touches.length === 1) {
                        // Pan gesture
                        const deltaX = e.touches[0].clientX - touchStartX;
                        const deltaY = e.touches[0].clientY - touchStartY;
                        vncOffsetX += deltaX * 0.5;
                        vncOffsetY += deltaY * 0.5;
                        touchStartX = e.touches[0].clientX;
                        touchStartY = e.touches[0].clientY;
                        applyVncTransform();
                    } else if (e.touches.length === 2) {
                        // Pinch zoom gesture
                        const dx = e.touches[0].clientX - e.touches[1].clientX;
                        const dy = e.touches[0].clientY - e.touches[1].clientY;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        const scale = (distance / touchStartDistance) * touchStartScale;
                        vncScale = Math.max(0.5, Math.min(3, scale));
                        applyVncTransform();
                    }
                    e.preventDefault();
                });

                // Initial show
                showMobileControls();
            }
        </script>
    </body>
    </html>
    """
    
    return vnc_viewer_html


def create_vnc_controls():
    """Create VNC viewer controls for the main interface"""

    with gr.Group():
        with gr.Row():
            browser_mode = gr.Radio(
                choices=[
                    ("🖥️ Navegador Local (Predeterminado)", "pc"),
                    ("📺 Visor Remoto VNC (Movil/Remoto)", "vnc")
                ],
                value="pc",
                label="🔧 Modo de Visualizacion",
                info="Selecciona donde mostrar la automatizacion del navegador"
            )

        with gr.Row():
            vnc_status = gr.Textbox(
                label="📊 Estado del Sistema",
                value="Modo Navegador Local - El navegador se abrira en tu computadora",
                interactive=False,
                scale=2
            )

        with gr.Row():
            vnc_open_btn = gr.Button(
                "🚀 Activar Visor VNC",
                variant="secondary",
                visible=False
            )
            vnc_close_btn = gr.Button(
                "⚡ Cerrar Visor VNC",
                variant="secondary",
                visible=False
            )
    
    # VNC viewer modal (hidden by default)
    vnc_modal = gr.HTML(
        value="",
        visible=False,
        elem_id="vnc-modal"
    )
    
    return {
        "browser_mode": browser_mode,
        "vnc_status": vnc_status,
        "vnc_open_btn": vnc_open_btn,
        "vnc_close_btn": vnc_close_btn,
        "vnc_modal": vnc_modal
    }


def handle_browser_mode_change(mode: str) -> tuple:
    """Handle browser mode change"""
    import platform

    if mode == "vnc":
        if platform.system().lower() == "windows":
            status = "🔧 Modo VNC - Navegador se mostrara en visor remoto (requiere WSL o Docker)"
        else:
            status = "🔧 Modo VNC - Navegador se mostrara en visor remoto (acceso movil)"
        open_visible = True
        close_visible = False
    else:  # mode == "pc"
        status = "🖥️ Modo Local - El navegador se abrira en tu computadora"
        open_visible = False
        close_visible = False

    return (
        gr.update(value=status),  # vnc_status
        gr.update(visible=open_visible),  # vnc_open_btn
        gr.update(visible=close_visible)  # vnc_close_btn
    )


def handle_vnc_open() -> tuple:
    """Handle opening VNC viewer - start VNC server if needed"""
    try:
        # Import VNC manager
        import asyncio
        import platform
        from src.vnc.vnc_server import vnc_manager

        # Try to start VNC server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            vnc_info = loop.run_until_complete(vnc_manager.start_server("browser_automation"))
            loop.close()

            if vnc_info and vnc_info.get("status") == "success":
                vnc_html = create_vnc_viewer_modal()

                # Inject VNC connection info
                vnc_html = vnc_html.replace(
                    "let vncPort = 5999;",
                    f"let vncPort = {vnc_info.get('port', 5999)};"
                )

                method = vnc_info.get('method', 'VNC')
                return (
                    gr.update(value=vnc_html, visible=True),  # vnc_modal
                    gr.update(visible=False),  # vnc_open_btn
                    gr.update(visible=True),   # vnc_close_btn
                    gr.update(value=f"VNC Viewer Open - {method} on Port {vnc_info.get('port')}")  # vnc_status
                )
            else:
                error_msg = vnc_info.get('error', 'Unknown error') if vnc_info else 'Failed to start VNC'
                suggestions = vnc_info.get('suggestions', []) if vnc_info else []

                status_msg = f"VNC Error: {error_msg}"
                if suggestions and platform.system().lower() == "windows":
                    status_msg += " | Run: python setup_windows_vnc.py"

                return (
                    gr.update(),  # vnc_modal
                    gr.update(),  # vnc_open_btn
                    gr.update(),  # vnc_close_btn
                    gr.update(value=status_msg)  # vnc_status
                )
        except Exception as e:
            loop.close()
            status_msg = f"VNC Error: {str(e)}"
            if platform.system().lower() == "windows":
                status_msg += " | Run: python setup_windows_vnc.py for setup"

            return (
                gr.update(),  # vnc_modal
                gr.update(),  # vnc_open_btn
                gr.update(),  # vnc_close_btn
                gr.update(value=status_msg)  # vnc_status
            )

    except Exception as e:
        import platform
        status_msg = f"VNC Error: {str(e)}"
        if platform.system().lower() == "windows":
            status_msg += " | Run: python setup_windows_vnc.py for setup"

        return (
            gr.update(),  # vnc_modal
            gr.update(),  # vnc_open_btn
            gr.update(),  # vnc_close_btn
            gr.update(value=status_msg)  # vnc_status
        )


def handle_vnc_close() -> tuple:
    """Handle closing VNC viewer"""
    return (
        gr.update(value="", visible=False),  # vnc_modal
        gr.update(visible=True),   # vnc_open_btn
        gr.update(visible=False),  # vnc_close_btn
        gr.update(value="VNC Viewer Closed")  # vnc_status
    )
