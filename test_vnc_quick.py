#!/usr/bin/env python3
"""
Test rápido para verificar que el VNC se visualice correctamente
"""

import asyncio
import logging
import subprocess
import sys
import time
import requests
import socket
import webbrowser
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickVNCTest:
    """Test rápido de VNC"""
    
    def __init__(self):
        self.test_port = 7792
        self.webui_process = None
        
    async def run_quick_test(self):
        """Ejecutar test rápido"""
        logger.info("⚡ AUTONOBOT - Test Rápido de VNC")
        logger.info("="*40)
        
        try:
            # Test 1: Verificar dependencias
            logger.info("🔍 1. Verificando dependencias...")
            if not await self.check_dependencies():
                return False
            
            # Test 2: Iniciar WebUI
            logger.info("🚀 2. Iniciando WebUI...")
            if not await self.start_webui():
                return False
            
            # Test 3: Verificar interfaz cyberpunk
            logger.info("🎨 3. Verificando interfaz cyberpunk...")
            if not await self.check_cyberpunk_interface():
                return False
            
            # Test 4: Probar VNC
            logger.info("📺 4. Probando funcionalidad VNC...")
            vnc_result = await self.test_vnc_functionality()
            
            # Test 5: Abrir navegador para verificación visual
            logger.info("🌐 5. Abriendo navegador para verificación...")
            await self.open_for_visual_check()
            
            # Resumen
            await self.show_summary(vnc_result)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en test rápido: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def check_dependencies(self) -> bool:
        """Verificar dependencias básicas"""
        try:
            # Verificar Gradio
            import gradio
            logger.info(f"  ✅ Gradio {gradio.__version__}")
            
            # Verificar requests
            import requests
            logger.info(f"  ✅ Requests disponible")
            
            # Verificar puerto disponible
            if self.is_port_available(self.test_port):
                logger.info(f"  ✅ Puerto {self.test_port} disponible")
            else:
                logger.error(f"  ❌ Puerto {self.test_port} ocupado")
                return False
            
            return True
            
        except ImportError as e:
            logger.error(f"  ❌ Dependencia faltante: {e}")
            return False
    
    async def start_webui(self) -> bool:
        """Iniciar WebUI"""
        try:
            self.webui_process = subprocess.Popen(
                [sys.executable, "webui.py", "--port", str(self.test_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar inicio
            logger.info("  ⏳ Esperando inicio del WebUI...")
            await asyncio.sleep(15)
            
            # Verificar que esté corriendo
            if self.webui_process.poll() is not None:
                stdout, stderr = self.webui_process.communicate()
                logger.error(f"  ❌ WebUI falló: {stderr.decode()}")
                return False
            
            # Test de conectividad
            try:
                response = requests.get(f"http://127.0.0.1:{self.test_port}", timeout=10)
                if response.status_code == 200:
                    logger.info("  ✅ WebUI iniciado correctamente")
                    return True
                else:
                    logger.error(f"  ❌ WebUI responde con código {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"  ❌ No se puede conectar al WebUI: {e}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error iniciando WebUI: {e}")
            return False
    
    async def check_cyberpunk_interface(self) -> bool:
        """Verificar interfaz cyberpunk"""
        try:
            response = requests.get(f"http://127.0.0.1:{self.test_port}", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"  ❌ Error HTTP: {response.status_code}")
                return False
            
            content = response.text
            
            # Verificar elementos cyberpunk
            cyberpunk_checks = [
                ("AUTONOBOT", "Título de la aplicación"),
                ("Navegador Autonomo", "Subtítulo en español"),
                ("--cyber-primary", "Variables CSS cyberpunk"),
                ("#00ffff", "Color cyan cyberpunk"),
                ("cyberpunk-glow", "Animaciones cyberpunk"),
                ("Orbitron", "Fuente cyberpunk"),
                ("Configuracion de Agente", "Localización española")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element, description in cyberpunk_checks:
                if element in content:
                    found_elements.append((element, description))
                    logger.info(f"    ✅ {description}")
                else:
                    missing_elements.append((element, description))
                    logger.warning(f"    ⚠️ Falta: {description}")
            
            success_rate = len(found_elements) / len(cyberpunk_checks)
            
            if success_rate >= 0.8:
                logger.info(f"  ✅ Interfaz cyberpunk OK ({success_rate*100:.0f}%)")
                return True
            else:
                logger.warning(f"  ⚠️ Interfaz cyberpunk incompleta ({success_rate*100:.0f}%)")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error verificando interfaz: {e}")
            return False
    
    async def test_vnc_functionality(self) -> Dict[str, Any]:
        """Probar funcionalidad VNC"""
        try:
            # Importar VNC manager
            from src.vnc.vnc_server import vnc_manager
            
            # Intentar iniciar VNC
            logger.info("  🔄 Iniciando servidor VNC...")
            vnc_result = await vnc_manager.start_server("quick_test")
            
            if vnc_result.get("status") == "success":
                port = vnc_result.get("port")
                method = vnc_result.get("method", "Desconocido")
                
                logger.info(f"  ✅ VNC iniciado en puerto {port} (método: {method})")
                
                # Test de conectividad
                if await self.test_vnc_connection(port):
                    logger.info("  ✅ Conectividad VNC OK")
                    return {
                        "success": True,
                        "port": port,
                        "method": method,
                        "connectivity": True
                    }
                else:
                    logger.warning("  ⚠️ VNC iniciado pero sin conectividad")
                    return {
                        "success": True,
                        "port": port,
                        "method": method,
                        "connectivity": False
                    }
            else:
                error = vnc_result.get("error", "Error desconocido")
                logger.warning(f"  ⚠️ VNC no pudo iniciar: {error}")
                return {
                    "success": False,
                    "error": error,
                    "suggestions": vnc_result.get("suggestions", [])
                }
                
        except Exception as e:
            logger.error(f"  ❌ Error en test VNC: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_vnc_connection(self, port: int) -> bool:
        """Probar conexión VNC"""
        try:
            # Test TCP
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    return True
            
            # Test HTTP (para mock server)
            try:
                response = requests.get(f"http://127.0.0.1:{port}", timeout=3)
                return response.status_code == 200
            except:
                pass
            
            return False
            
        except Exception:
            return False
    
    async def open_for_visual_check(self):
        """Abrir navegador para verificación visual"""
        try:
            url = f"http://127.0.0.1:{self.test_port}"
            logger.info(f"  🌐 Abriendo: {url}")
            webbrowser.open(url)
            
            logger.info("  👀 Verifica visualmente:")
            logger.info("    - Interfaz cyberpunk (colores neón, efectos)")
            logger.info("    - Textos en español")
            logger.info("    - Funcionalidad VNC en 'Agente Interactivo'")
            
        except Exception as e:
            logger.warning(f"  ⚠️ No se pudo abrir navegador: {e}")
            logger.info(f"  🔗 Abrir manualmente: http://127.0.0.1:{self.test_port}")
    
    async def show_summary(self, vnc_result: Dict[str, Any]):
        """Mostrar resumen del test"""
        logger.info("\n" + "="*50)
        logger.info("📊 RESUMEN DEL TEST RÁPIDO")
        logger.info("="*50)
        
        # Estado general
        if vnc_result.get("success", False):
            logger.info("🎉 Estado general: ✅ EXITOSO")
        else:
            logger.info("⚠️ Estado general: ❌ CON PROBLEMAS")
        
        # Detalles VNC
        if vnc_result.get("success", False):
            logger.info(f"📺 VNC: ✅ Funcionando en puerto {vnc_result.get('port')}")
            logger.info(f"🔧 Método: {vnc_result.get('method', 'Desconocido')}")
            
            if vnc_result.get("connectivity", False):
                logger.info("🌐 Conectividad: ✅ OK")
            else:
                logger.info("🌐 Conectividad: ⚠️ Limitada")
        else:
            logger.info("📺 VNC: ❌ No funciona")
            if "error" in vnc_result:
                logger.info(f"🐛 Error: {vnc_result['error']}")
        
        # Instrucciones
        logger.info("\n💡 PRÓXIMOS PASOS:")
        logger.info("1. 🖱️ Ve a la pestaña 'Agente Interactivo'")
        logger.info("2. 🔄 Cambia a 'Visor Remoto VNC'")
        logger.info("3. 🚀 Haz clic en 'Activar Visor VNC'")
        logger.info("4. 👀 Verifica que se abra el visor con tema cyberpunk")
        
        if not vnc_result.get("success", False):
            logger.info("\n🛠️ SOLUCIÓN DE PROBLEMAS:")
            logger.info("- En Windows: Ejecuta 'python setup_windows_vnc.py'")
            logger.info("- Verifica que no hay firewall bloqueando")
            logger.info("- Intenta reiniciar la aplicación")
        
        # Esperar input del usuario
        input("\n📱 Presiona Enter cuando hayas terminado la verificación visual...")
    
    def is_port_available(self, port: int) -> bool:
        """Verificar si puerto está disponible"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    async def cleanup(self):
        """Limpiar recursos"""
        logger.info("\n🧹 Limpiando recursos...")
        
        # Detener WebUI
        if self.webui_process:
            try:
                self.webui_process.terminate()
                self.webui_process.wait(timeout=5)
                logger.info("✅ WebUI detenido")
            except:
                try:
                    self.webui_process.kill()
                except:
                    pass
        
        # Detener VNC
        try:
            from src.vnc.vnc_server import vnc_manager
            await vnc_manager.stop_server("quick_test")
            logger.info("✅ VNC detenido")
        except:
            pass


async def main():
    """Función principal"""
    print("⚡ AUTONOBOT - Test Rápido de Visualización VNC")
    print("=" * 45)
    print("Este test verifica rápidamente que el VNC funcione correctamente")
    print("=" * 45)
    
    test = QuickVNCTest()
    success = await test.run_quick_test()
    
    if success:
        print("\n🎉 Test completado. Revisa la ventana del navegador.")
    else:
        print("\n❌ Test falló. Revisa los errores arriba.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelado")
    except Exception as e:
        print(f"\n❌ Error: {e}")
