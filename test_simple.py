#!/usr/bin/env python3
"""
Test simple para verificar que todo funciona
"""

print("🔍 Iniciando test simple...")

try:
    print("📦 Importando Gradio...")
    import gradio as gr
    print(f"✅ Gradio {gr.__version__} importado")
    
    print("📦 Importando configuración...")
    from src.utils.default_config_settings import default_config
    config = default_config()
    print(f"✅ Configuración cargada: {config.get('llm_provider', 'N/A')}")
    
    print("🎨 Creando interfaz simple...")
    def test_function(text):
        return f"AUTONOBOT dice: {text}"
    
    demo = gr.Interface(
        fn=test_function,
        inputs=gr.Textbox(placeholder="Escribe algo..."),
        outputs="text",
        title="🛡️ AUTONOBOT - Test Simple",
        description="Prueba de funcionamiento básico"
    )
    
    print("✅ Interfaz creada")
    print("🚀 Lanzando en puerto 7788...")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7788,
        share=False,
        inbrowser=True,
        prevent_thread_lock=False
    )
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
