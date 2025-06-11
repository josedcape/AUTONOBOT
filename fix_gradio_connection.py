#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar problemas de conexión con Gradio
"""

import sys
import socket
import subprocess
import time
import traceback
import os

def check_port_availability(port):
    """Verificar si un puerto está disponible"""
    print(f"🔍 Verificando disponibilidad del puerto {port}...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"❌ Puerto {port} está ocupado")
                return False
            else:
                print(f"✅ Puerto {port} está disponible")
                return True
    except Exception as e:
        print(f"⚠️ Error verificando puerto {port}: {e}")
        return True

def kill_processes_on_port(port):
    """Terminar procesos que usan un puerto específico"""
    print(f"🔧 Intentando liberar puerto {port}...")
    
    try:
        # En Windows
        if os.name == 'nt':
            # Encontrar procesos usando el puerto
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            lines = result.stdout.split('\n')
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        print(f"🔫 Terminando proceso PID {pid} en puerto {port}")
                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                     capture_output=True)
        else:
            # En Linux/Mac
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    print(f"🔫 Terminando proceso PID {pid} en puerto {port}")
                    subprocess.run(['kill', '-9', pid], capture_output=True)
                    
        time.sleep(2)  # Esperar a que se libere el puerto
        
    except Exception as e:
        print(f"⚠️ Error liberando puerto {port}: {e}")

def test_gradio_simple():
    """Probar Gradio con una interfaz muy simple"""
    print("\n🧪 Probando Gradio con interfaz simple...")
    
    try:
        import gradio as gr
        
        def hello(name):
            return f"Hola {name}!"
        
        # Crear interfaz simple
        demo = gr.Interface(
            fn=hello, 
            inputs=gr.Textbox(placeholder="Escribe tu nombre"), 
            outputs="text",
            title="Test AUTONOBOT",
            description="Prueba de conexión"
        )
        
        print("✅ Interfaz Gradio simple creada")
        return demo
        
    except Exception as e:
        print(f"❌ Error creando interfaz Gradio: {e}")
        traceback.print_exc()
        return None

def launch_with_retry(demo, port=7788, max_retries=3):
    """Lanzar Gradio con reintentos"""
    print(f"\n🚀 Intentando lanzar servidor en puerto {port}...")
    
    for attempt in range(max_retries):
        try:
            print(f"📡 Intento {attempt + 1}/{max_retries}")
            
            # Verificar y liberar puerto si es necesario
            if not check_port_availability(port):
                kill_processes_on_port(port)
                time.sleep(2)
            
            # Intentar lanzar
            demo.launch(
                server_name="127.0.0.1",
                server_port=port,
                share=False,
                inbrowser=False,
                prevent_thread_lock=False,
                show_error=True,
                quiet=False
            )
            
            print(f"✅ Servidor lanzado exitosamente en puerto {port}")
            return True
            
        except Exception as e:
            print(f"❌ Intento {attempt + 1} falló: {e}")
            if attempt < max_retries - 1:
                port += 1  # Probar siguiente puerto
                print(f"🔄 Probando puerto {port}...")
                time.sleep(2)
            else:
                print("💥 Todos los intentos fallaron")
                traceback.print_exc()
                return False
    
    return False

def fix_gradio_config():
    """Intentar arreglar configuración de Gradio"""
    print("\n🔧 Verificando configuración de Gradio...")
    
    try:
        import gradio as gr
        print(f"✅ Gradio versión: {gr.__version__}")
        
        # Verificar configuración
        print("🔍 Verificando configuración de red...")
        
        # Limpiar caché de Gradio si existe
        gradio_cache_dir = os.path.expanduser("~/.gradio")
        if os.path.exists(gradio_cache_dir):
            print(f"🧹 Limpiando caché de Gradio: {gradio_cache_dir}")
            try:
                import shutil
                shutil.rmtree(gradio_cache_dir)
                print("✅ Caché limpiado")
            except Exception as e:
                print(f"⚠️ No se pudo limpiar caché: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración de Gradio: {e}")
        return False

def main():
    """Función principal de diagnóstico y reparación"""
    print("🩺 DIAGNÓSTICO Y REPARACIÓN DE CONEXIÓN GRADIO")
    print("=" * 60)
    
    # 1. Verificar configuración de Gradio
    if not fix_gradio_config():
        print("\n❌ Fallo en configuración de Gradio. Abortando.")
        return
    
    # 2. Verificar puertos
    ports_to_check = [7788, 7789, 7790, 7791]
    available_port = None
    
    for port in ports_to_check:
        if check_port_availability(port):
            available_port = port
            break
        else:
            kill_processes_on_port(port)
            time.sleep(1)
            if check_port_availability(port):
                available_port = port
                break
    
    if not available_port:
        print("❌ No se pudo encontrar un puerto disponible")
        return
    
    print(f"✅ Usando puerto {available_port}")
    
    # 3. Probar interfaz simple
    demo = test_gradio_simple()
    if not demo:
        print("\n❌ No se pudo crear interfaz de prueba")
        return
    
    # 4. Lanzar con reintentos
    if launch_with_retry(demo, available_port):
        print(f"\n🎉 ¡Éxito! Servidor funcionando en http://127.0.0.1:{available_port}")
        print("🌐 Abre tu navegador y ve a la URL de arriba")
        print("⏹️ Presiona Ctrl+C para detener el servidor")
        
        try:
            # Mantener servidor activo
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido por el usuario")
            demo.close()
    else:
        print("\n💥 No se pudo lanzar el servidor")
        
        # Sugerir soluciones
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("1. Reiniciar el sistema")
        print("2. Verificar firewall/antivirus")
        print("3. Reinstalar Gradio: pip uninstall gradio && pip install gradio")
        print("4. Usar un puerto diferente")

if __name__ == "__main__":
    main()
