#!/usr/bin/env python3
"""
Script robusto para iniciar AUTONOBOT con manejo de errores mejorado
"""

import sys
import os
import time
import socket
import subprocess
import traceback

def check_port(port):
    """Verificar si un puerto está disponible"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result != 0
    except:
        return True

def kill_port_processes(port):
    """Terminar procesos en un puerto específico"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['netstat', '-ano'], capture_output=True, timeout=5)
        else:  # Linux/Mac
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    subprocess.run(['kill', '-9', pid], capture_output=True)
        time.sleep(2)
    except:
        pass

def start_autonobot():
    """Iniciar AUTONOBOT con configuración robusta"""
    
    print("🛡️ AUTONOBOT - AGENTE DE NAVEGACIÓN AUTÓNOMA")
    print("=" * 60)
    print("🚀 Iniciando con configuración robusta...")
    
    # Verificar dependencias
    print("🔍 Verificando dependencias...")
    try:
        import gradio as gr
        print(f"✅ Gradio {gr.__version__} disponible")
    except ImportError:
        print("❌ Gradio no encontrado. Instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'gradio'])
        import gradio as gr
    
    # Verificar puerto
    port = 7788
    print(f"🔍 Verificando puerto {port}...")
    
    if not check_port(port):
        print(f"⚠️ Puerto {port} ocupado. Liberando...")
        kill_port_processes(port)
        time.sleep(2)
        
        if not check_port(port):
            port = 7789
            print(f"🔄 Usando puerto alternativo {port}")
    
    print(f"✅ Puerto {port} disponible")
    
    # Configurar variables de entorno
    os.environ['GRADIO_SERVER_PORT'] = str(port)
    os.environ['GRADIO_SERVER_NAME'] = '127.0.0.1'
    
    # Importar y configurar AUTONOBOT
    print("🔧 Configurando AUTONOBOT...")
    
    try:
        # Importar módulos necesarios
        from src.utils.default_config_settings import default_config
        import webui
        
        print("✅ Módulos importados correctamente")
        
        # Obtener configuración
        config = default_config()
        print(f"✅ Configuración cargada (LLM: {config.get('llm_provider', 'N/A')})")
        
        # Crear interfaz
        print("🎨 Creando interfaz futurista...")
        demo = webui.create_ui(config, theme_name="Ocean")
        print("✅ Interfaz creada exitosamente")
        
        # Lanzar servidor
        print(f"🚀 Lanzando servidor en http://127.0.0.1:{port}")
        print("📱 Características:")
        print("   ● Chat Interactivo Listo")
        print("   ● Soporte Multi-Tarea")
        print("   ● Control en Tiempo Real")
        print("   ● 9 Modelos Gemini Disponibles")
        print("   ● Interfaz Completamente en Español")
        print()
        print("🌐 Abre tu navegador en la URL de arriba")
        print("🛑 Presiona Ctrl+C para detener")
        print("=" * 60)
        
        # Configuración de lanzamiento robusta
        launch_config = {
            'server_name': '127.0.0.1',
            'server_port': port,
            'share': False,
            'inbrowser': True,
            'prevent_thread_lock': False,
            'show_error': True,
            'quiet': False,
            'favicon_path': None
        }
        
        # Intentar lanzar
        demo.launch(**launch_config)
        
    except KeyboardInterrupt:
        print("\n🛑 AUTONOBOT detenido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error al iniciar AUTONOBOT: {e}")
        print("\n🔧 Información de debug:")
        traceback.print_exc()
        
        print("\n💡 Soluciones sugeridas:")
        print("1. Reiniciar el terminal/sistema")
        print("2. Verificar firewall/antivirus")
        print("3. Reinstalar dependencias:")
        print("   pip uninstall gradio && pip install gradio")
        print("4. Ejecutar script de diagnóstico:")
        print("   python fix_gradio_connection.py")

def main():
    """Función principal"""
    try:
        start_autonobot()
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        traceback.print_exc()
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
