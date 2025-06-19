import gradio as gr

from src.webui.webui_manager import WebuiManager
from src.webui.components.agent_settings_tab import create_agent_settings_tab
from src.webui.components.browser_settings_tab import create_browser_settings_tab
from src.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
# from src.webui.components.deep_research_agent_tab import create_deep_research_agent_tab  # Temporarily disabled
from src.webui.components.load_save_config_tab import create_load_save_config_tab

theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base()
}


def create_ui(theme_name="Ocean"):
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Exo+2:wght@300;400;500;600;700;800;900&family=Electrolize:wght@400&display=swap');

    /* Cyberpunk Color Variables */
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

    /* Main Container Styling */
    .gradio-container {
        width: 70vw !important;
        max-width: 70% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
        background: linear-gradient(135deg, var(--cyber-dark) 0%, var(--cyber-dark-secondary) 100%) !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* Header Styling */
    .header-text {
        text-align: center;
        margin-bottom: 30px;
        font-family: 'Orbitron', monospace !important;
        color: var(--cyber-text) !important;
        text-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    .header-text h1 {
        font-size: 4rem !important;
        font-weight: 900 !important;
        font-family: 'Orbitron', 'Exo 2', 'Rajdhani', monospace !important;
        background: linear-gradient(135deg, var(--cyber-primary) 0%, var(--cyber-secondary) 50%, var(--cyber-accent) 100%) !important;
        background-size: 300% 300% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: cyberpunk-title-glow 4s ease-in-out infinite alternate !important;
        margin-bottom: 15px !important;
        letter-spacing: 4px !important;
        text-transform: uppercase !important;
        filter: brightness(1.2) contrast(1.1) !important;
        text-rendering: optimizeLegibility !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }

    .header-text h2 {
        color: var(--cyber-text) !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        font-family: 'Rajdhani', 'Exo 2', sans-serif !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        margin-bottom: 20px !important;
        text-shadow:
            0 0 10px var(--cyber-accent),
            0 0 20px var(--cyber-accent),
            0 0 30px var(--cyber-accent) !important;
        animation: subtitle-pulse 3s ease-in-out infinite alternate !important;
        filter: brightness(1.1) !important;
        text-rendering: optimizeLegibility !important;
        -webkit-font-smoothing: antialiased !important;
    }

    .header-text h4 {
        color: var(--cyber-text-dim) !important;
        font-weight: 400 !important;
        font-size: 1rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* Enhanced Cyberpunk Animations */
    @keyframes cyberpunk-title-glow {
        0% {
            background-position: 0% 50%;
            filter: brightness(1.2) contrast(1.1) hue-rotate(0deg);
        }
        50% {
            background-position: 100% 50%;
            filter: brightness(1.4) contrast(1.2) hue-rotate(10deg);
        }
        100% {
            background-position: 0% 50%;
            filter: brightness(1.2) contrast(1.1) hue-rotate(0deg);
        }
    }

    @keyframes subtitle-pulse {
        0% {
            text-shadow:
                0 0 5px var(--cyber-accent),
                0 0 10px var(--cyber-accent),
                0 0 15px var(--cyber-accent);
            transform: scale(1);
        }
        100% {
            text-shadow:
                0 0 10px var(--cyber-accent),
                0 0 20px var(--cyber-accent),
                0 0 30px var(--cyber-accent),
                0 0 40px var(--cyber-accent);
            transform: scale(1.02);
        }
    }

    /* Tab Styling */
    .tab-nav {
        background: var(--cyber-dark-tertiary) !important;
        border: 1px solid var(--cyber-primary) !important;
        border-radius: 12px !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    .tab-nav button {
        background: transparent !important;
        color: var(--cyber-text) !important;
        border: none !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .tab-nav button:hover {
        color: var(--cyber-primary) !important;
        text-shadow: var(--cyber-glow) var(--cyber-primary) !important;
        transform: translateY(-2px) !important;
    }

    .tab-nav button.selected {
        background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary)) !important;
        color: var(--cyber-dark) !important;
        font-weight: 700 !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    /* Panel and Group Styling */
    .block, .form {
        background: var(--cyber-dark-tertiary) !important;
        border: 1px solid var(--cyber-primary) !important;
        border-radius: 12px !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
        margin-bottom: 20px !important;
        padding: 20px !important;
    }

    .tab-header-text {
        text-align: center;
        color: var(--cyber-text) !important;
        font-family: 'Orbitron', monospace !important;
        text-shadow: var(--cyber-glow) var(--cyber-accent) !important;
    }

    .theme-section {
        margin-bottom: 15px;
        padding: 20px;
        border-radius: 12px;
        background: var(--cyber-dark-secondary) !important;
        border: 1px solid var(--cyber-purple) !important;
        box-shadow: var(--cyber-glow) var(--cyber-purple) !important;
    }

    /* Button Styling */
    button {
        background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary)) !important;
        color: var(--cyber-dark) !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
        cursor: pointer !important;
    }

    button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px var(--cyber-primary) !important;
        background: linear-gradient(45deg, var(--cyber-secondary), var(--cyber-accent)) !important;
    }

    button:active {
        transform: translateY(0) !important;
    }

    button.secondary {
        background: linear-gradient(45deg, var(--cyber-purple), var(--cyber-dark-tertiary)) !important;
        color: var(--cyber-text) !important;
    }

    button.secondary:hover {
        background: linear-gradient(45deg, var(--cyber-accent), var(--cyber-purple)) !important;
    }

    /* Input Styling */
    input, textarea, select {
        background: var(--cyber-dark-secondary) !important;
        border: 2px solid var(--cyber-primary) !important;
        border-radius: 8px !important;
        color: var(--cyber-text) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1rem !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
    }

    input:focus, textarea:focus, select:focus {
        border-color: var(--cyber-secondary) !important;
        box-shadow: var(--cyber-glow) var(--cyber-secondary) !important;
        outline: none !important;
    }

    input::placeholder, textarea::placeholder {
        color: var(--cyber-text-dim) !important;
        font-style: italic !important;
    }

    /* Label Styling */
    label {
        color: var(--cyber-text) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin-bottom: 8px !important;
        display: block !important;
    }

    /* Checkbox and Radio Styling */
    input[type="checkbox"], input[type="radio"] {
        accent-color: var(--cyber-primary) !important;
        transform: scale(1.2) !important;
    }

    /* Slider Styling */
    input[type="range"] {
        background: var(--cyber-dark-secondary) !important;
        border-radius: 8px !important;
        height: 8px !important;
    }

    input[type="range"]::-webkit-slider-thumb {
        background: var(--cyber-primary) !important;
        border-radius: 50% !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    /* Dropdown Styling */
    .dropdown {
        background: var(--cyber-dark-secondary) !important;
        border: 2px solid var(--cyber-primary) !important;
        border-radius: 8px !important;
        color: var(--cyber-text) !important;
    }

    /* File Upload Styling */
    .file-upload {
        background: var(--cyber-dark-tertiary) !important;
        border: 2px dashed var(--cyber-accent) !important;
        border-radius: 12px !important;
        color: var(--cyber-text) !important;
        text-align: center !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
    }

    .file-upload:hover {
        border-color: var(--cyber-primary) !important;
        background: var(--cyber-dark-secondary) !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    /* Progress Bar Styling */
    .progress {
        background: var(--cyber-dark-secondary) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5) !important;
    }

    .progress-bar {
        background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-accent)) !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
        animation: progress-glow 2s ease-in-out infinite alternate !important;
    }

    @keyframes progress-glow {
        0% { box-shadow: 0 0 5px var(--cyber-primary); }
        100% { box-shadow: 0 0 20px var(--cyber-primary), 0 0 30px var(--cyber-accent); }
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 12px !important;
        background: var(--cyber-dark) !important;
    }

    ::-webkit-scrollbar-track {
        background: var(--cyber-dark-secondary) !important;
        border-radius: 6px !important;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary)) !important;
        border-radius: 6px !important;
        box-shadow: var(--cyber-glow) var(--cyber-primary) !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, var(--cyber-secondary), var(--cyber-accent)) !important;
    }

    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .gradio-container {
            width: 95vw !important;
            max-width: 95% !important;
            padding: 5px !important;
        }

        .header-text h1 {
            font-size: 2.5rem !important;
        }

        .header-text h3 {
            font-size: 1rem !important;
        }

        button {
            padding: 10px 16px !important;
            font-size: 0.9rem !important;
        }

        .tab-nav button {
            font-size: 0.9rem !important;
            padding: 8px 12px !important;
        }

        .block, .form {
            padding: 15px !important;
            margin-bottom: 15px !important;
        }
    }

    /* Tablet Responsive Design */
    @media (max-width: 1024px) and (min-width: 769px) {
        .gradio-container {
            width: 85vw !important;
            max-width: 85% !important;
        }

        .header-text h1 {
            font-size: 3rem !important;
        }
    }

    /* Additional Cyberpunk Effects */
    .block:hover, .form:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 25px var(--cyber-primary) !important;
        transition: all 0.3s ease !important;
    }

    /* Loading Animation */
    @keyframes cyber-loading {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }

    .loading {
        animation: cyber-loading 1.5s ease-in-out infinite !important;
    }

    /* Success/Error States */
    .success {
        border-color: var(--cyber-accent) !important;
        box-shadow: var(--cyber-glow) var(--cyber-accent) !important;
    }

    .error {
        border-color: #ff0040 !important;
        box-shadow: var(--cyber-glow) #ff0040 !important;
    }

    /* Chat/Message Styling */
    .message {
        background: var(--cyber-dark-tertiary) !important;
        border: 1px solid var(--cyber-primary) !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        color: var(--cyber-text) !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    .message.user {
        border-color: var(--cyber-secondary) !important;
        background: linear-gradient(45deg, var(--cyber-dark-secondary), var(--cyber-dark-tertiary)) !important;
    }

    .message.assistant {
        border-color: var(--cyber-accent) !important;
        background: linear-gradient(45deg, var(--cyber-dark-tertiary), var(--cyber-dark-secondary)) !important;
    }

    /* Mobile Floating Action Buttons (FABs) */
    .fab-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        display: none; /* Hidden by default, shown on mobile */
    }

    .fab {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary));
        border: none;
        color: var(--cyber-dark);
        font-size: 24px;
        cursor: pointer;
        margin-bottom: 16px;
        box-shadow:
            0 4px 8px rgba(0, 0, 0, 0.3),
            var(--cyber-glow) var(--cyber-primary);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }

    .fab:hover {
        transform: scale(1.1);
        box-shadow:
            0 6px 12px rgba(0, 0, 0, 0.4),
            0 0 20px var(--cyber-primary);
    }

    .fab:active {
        transform: scale(0.95);
    }

    .fab.secondary {
        background: linear-gradient(45deg, var(--cyber-purple), var(--cyber-accent));
        box-shadow:
            0 4px 8px rgba(0, 0, 0, 0.3),
            var(--cyber-glow) var(--cyber-purple);
    }

    .fab.secondary:hover {
        box-shadow:
            0 6px 12px rgba(0, 0, 0, 0.4),
            0 0 20px var(--cyber-purple);
    }

    /* Enhanced Mobile Touch Optimizations */
    @media (max-width: 768px) {
        .fab-container {
            display: block;
        }

        /* Larger touch targets */
        button, .tab-nav button {
            min-height: 44px !important;
            min-width: 44px !important;
            padding: 12px 20px !important;
            font-size: 14px !important;
        }

        /* Improved touch feedback */
        button:active, .tab-nav button:active {
            transform: scale(0.95) !important;
            transition: transform 0.1s ease !important;
        }

        /* Better spacing for touch */
        .block, .form {
            margin-bottom: 20px !important;
            padding: 20px !important;
        }

        /* Optimized input fields for mobile */
        input, textarea, select {
            min-height: 44px !important;
            font-size: 16px !important; /* Prevents zoom on iOS */
            padding: 12px 16px !important;
        }

        /* Mobile-friendly tabs */
        .tab-nav {
            overflow-x: auto !important;
            white-space: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
            padding-bottom: 10px !important;
        }

        .tab-nav button {
            flex-shrink: 0 !important;
            margin-right: 8px !important;
            white-space: nowrap !important;
        }

        /* Mobile header adjustments */
        .header-text h1 {
            font-size: 2.5rem !important;
            line-height: 1.2 !important;
        }

        .header-text h2 {
            font-size: 1.4rem !important;
            line-height: 1.3 !important;
        }
    }

    /* Touch device specific optimizations */
    @media (hover: none) and (pointer: coarse) {
        .fab-container {
            display: block !important;
        }

        /* Disable hover effects on touch devices */
        button:hover, .tab-nav button:hover {
            transform: none !important;
        }

        /* Enhanced touch feedback */
        button:active {
            transform: scale(0.95) !important;
            background: linear-gradient(45deg, var(--cyber-secondary), var(--cyber-accent)) !important;
        }

        /* Better touch targets */
        .tab-nav button {
            padding: 14px 18px !important;
        }
    }
    """

    # dark mode in default
    js_func = """
    function refresh() {
        const url = new URL(window.location);

        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
            title="AUTONOBOT", theme=theme_map[theme_name], css=css, js=js_func,
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🤖 AUTONOBOT
                ## Navegador Autonomo Avanzado
                #### 🔮 INTERACTIVE CHAT READY • 🚀 MULTI-TASK SUPPORT • ⚡ REAL-TIME CONTROL 🔮
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("🔧 Configuración de Agente"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 Configuración del Navegador"):
                create_browser_settings_tab(ui_manager)

            with gr.TabItem("🤖 Agente Interactivo"):
                create_browser_use_agent_tab(ui_manager)

            with gr.TabItem("📊 Cola de Tareas"):
                gr.Markdown(
                    """
                    ### 🚀 Sistema de Gestión de Tareas
                    #### Monitoreo y control de procesos automatizados
                    """,
                    elem_classes=["tab-header-text"],
                )
                with gr.Tabs():
                    with gr.TabItem("📈 Estado del Sistema"):
                        gr.Markdown("**Sistema de investigación profunda temporalmente deshabilitado para compatibilidad.**")
                    # with gr.TabItem("Deep Research"):
                    #     create_deep_research_agent_tab(ui_manager)  # Temporarily disabled

            with gr.TabItem("💾 Resultados"):
                gr.Markdown(
                    """
                    ### 📊 Análisis de Resultados
                    #### Historial y métricas de rendimiento
                    """,
                    elem_classes=["tab-header-text"],
                )

            with gr.TabItem("🎛️ Grabaciones"):
                gr.Markdown(
                    """
                    ### 📹 Archivo de Grabaciones
                    #### Sesiones guardadas y reproducciones
                    """,
                    elem_classes=["tab-header-text"],
                )

            with gr.TabItem("⚙️ Configuración"):
                create_load_save_config_tab(ui_manager)

        # Mobile Floating Action Buttons
        gr.HTML("""
            <div class="fab-container" id="fab-container">
                <button class="fab" id="fab-vnc" title="Activar VNC" onclick="toggleVNC()">
                    📺
                </button>
                <button class="fab secondary" id="fab-agent" title="Agente Interactivo" onclick="goToAgent()">
                    🤖
                </button>
                <button class="fab" id="fab-config" title="Configuración" onclick="goToConfig()">
                    ⚙️
                </button>
            </div>

            <script>
                // Mobile FAB functionality
                function toggleVNC() {
                    // Switch to VNC mode
                    const tabs = document.querySelectorAll('.tab-nav button');
                    tabs.forEach(tab => {
                        if (tab.textContent.includes('Agente Interactivo')) {
                            tab.click();
                            setTimeout(() => {
                                const vncRadio = document.querySelector('input[value="vnc"]');
                                if (vncRadio) {
                                    vncRadio.click();
                                    setTimeout(() => {
                                        const vncButton = document.querySelector('button[title*="VNC"], button[title*="Visor"]');
                                        if (vncButton) vncButton.click();
                                    }, 500);
                                }
                            }, 500);
                        }
                    });
                }

                function goToAgent() {
                    const tabs = document.querySelectorAll('.tab-nav button');
                    tabs.forEach(tab => {
                        if (tab.textContent.includes('Agente Interactivo')) {
                            tab.click();
                        }
                    });
                }

                function goToConfig() {
                    const tabs = document.querySelectorAll('.tab-nav button');
                    tabs.forEach(tab => {
                        if (tab.textContent.includes('Configuración')) {
                            tab.click();
                        }
                    });
                }

                // Show/hide FABs based on screen size
                function updateFABVisibility() {
                    const fabContainer = document.getElementById('fab-container');
                    if (fabContainer) {
                        if (window.innerWidth <= 768 ||
                            (navigator.maxTouchPoints > 0 && window.innerWidth <= 1024)) {
                            fabContainer.style.display = 'block';
                        } else {
                            fabContainer.style.display = 'none';
                        }
                    }
                }

                // Initialize FAB visibility
                document.addEventListener('DOMContentLoaded', updateFABVisibility);
                window.addEventListener('resize', updateFABVisibility);

                // Touch feedback for better mobile experience
                document.addEventListener('touchstart', function(e) {
                    if (e.target.classList.contains('fab')) {
                        e.target.style.transform = 'scale(0.95)';
                    }
                });

                document.addEventListener('touchend', function(e) {
                    if (e.target.classList.contains('fab')) {
                        setTimeout(() => {
                            e.target.style.transform = 'scale(1)';
                        }, 100);
                    }
                });
            </script>
            """)

        # Start task processor when demo loads
        async def start_task_processor():
            await ui_manager.start_task_processor()

        demo.load(fn=start_task_processor, inputs=[], outputs=[])

    return demo
