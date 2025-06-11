#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en webui.py
"""

import sys
import traceback

def test_imports():
    """Probar todas las importaciones"""
    print("🔍 Probando importaciones...")
    
    try:
        import gradio as gr
        print("✅ Gradio importado correctamente")
    except Exception as e:
        print(f"❌ Error importando Gradio: {e}")
        return False
    
    try:
        from src.utils.default_config_settings import default_config
        print("✅ default_config importado correctamente")
    except Exception as e:
        print(f"❌ Error importando default_config: {e}")
        return False
    
    try:
        from src.utils import utils
        print("✅ utils importado correctamente")
    except Exception as e:
        print(f"❌ Error importando utils: {e}")
        return False
    
    return True

def test_config():
    """Probar la configuración por defecto"""
    print("\n🔍 Probando configuración...")
    
    try:
        from src.utils.default_config_settings import default_config
        config = default_config()
        print(f"✅ Configuración cargada: {len(config)} elementos")
        print(f"   - LLM Provider: {config.get('llm_provider', 'N/A')}")
        print(f"   - LLM Model: {config.get('llm_model_name', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        traceback.print_exc()
        return False

def test_simple_gradio():
    """Probar una interfaz Gradio simple"""
    print("\n🔍 Probando interfaz Gradio simple...")
    
    try:
        import gradio as gr
        
        def hello(name):
            return f"Hola {name}!"
        
        demo = gr.Interface(fn=hello, inputs="text", outputs="text")
        print("✅ Interfaz Gradio simple creada")
        
        # Intentar lanzar en un puerto diferente para probar
        print("🚀 Intentando lanzar en puerto 7789...")
        demo.launch(server_port=7789, share=False, inbrowser=False, prevent_thread_lock=True)
        print("✅ Servidor Gradio simple funcionando en puerto 7789")
        demo.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con Gradio simple: {e}")
        traceback.print_exc()
        return False

def test_webui_creation():
    """Probar la creación de la interfaz webui"""
    print("\n🔍 Probando creación de interfaz webui...")
    
    try:
        # Importar solo lo necesario
        sys.path.append('.')
        from src.utils.default_config_settings import default_config
        
        # Obtener configuración
        config = default_config()
        print("✅ Configuración obtenida")
        
        # Intentar importar la función create_ui
        import webui
        print("✅ webui.py importado")
        
        # Intentar crear la interfaz
        print("🔧 Creando interfaz...")
        demo = webui.create_ui(config, theme_name="Dark")
        print("✅ Interfaz webui creada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando interfaz webui: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de diagnóstico"""
    print("🩺 DIAGNÓSTICO DE AUTONOBOT WEBUI")
    print("=" * 50)
    
    # Probar importaciones
    if not test_imports():
        print("\n❌ Fallo en importaciones. Abortando.")
        return
    
    # Probar configuración
    if not test_config():
        print("\n❌ Fallo en configuración. Abortando.")
        return
    
    # Probar Gradio simple
    if not test_simple_gradio():
        print("\n❌ Fallo en Gradio simple. Problema con Gradio.")
        return
    
    # Probar creación de webui
    if not test_webui_creation():
        print("\n❌ Fallo en creación de webui. Problema en webui.py.")
        return
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("🚀 Intentando lanzar webui completo...")
    
    try:
        import webui
        webui.main()
    except Exception as e:
        print(f"❌ Error lanzando webui: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
