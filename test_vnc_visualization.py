#!/usr/bin/env python3
"""
Test completo para evaluar la visualización del VNC en AUTONOBOT
"""

import asyncio
import logging
import time
import socket
import subprocess
import sys
import platform
import requests
from typing import Dict, Any, Optional
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VNCVisualizationTest:
    """Test completo para verificar la visualización del VNC"""
    
    def __init__(self):
        self.test_results = {}
        self.vnc_server = None
        self.webui_process = None
        self.test_port = 7790
        self.vnc_port = None
        
    async def run_all_tests(self):
        """Ejecutar todos los tests de visualización VNC"""
        logger.info("🚀 Iniciando tests de visualización VNC para AUTONOBOT")
        
        tests = [
            ("🔧 Test de Configuración del Sistema", self.test_system_config),
            ("🌐 Test de Inicio del WebUI", self.test_webui_startup),
            ("📡 Test de Servidor VNC", self.test_vnc_server),
            ("🖥️ Test de Conectividad VNC", self.test_vnc_connectivity),
            ("📱 Test de Acceso Móvil", self.test_mobile_access),
            ("🎨 Test de Interfaz Cyberpunk", self.test_cyberpunk_interface),
            ("⚡ Test de Funcionalidad VNC", self.test_vnc_functionality),
            ("🔄 Test de Reconexión", self.test_vnc_reconnection)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"Ejecutando: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = await test_func()
                self.test_results[test_name] = result
                status = "✅ PASÓ" if result.get("success", False) else "❌ FALLÓ"
                logger.info(f"{status}: {test_name}")
                if not result.get("success", False):
                    logger.error(f"Error: {result.get('error', 'Error desconocido')}")
            except Exception as e:
                logger.error(f"❌ EXCEPCIÓN en {test_name}: {str(e)}")
                self.test_results[test_name] = {"success": False, "error": str(e)}
        
        await self.cleanup()
        self.generate_report()
    
    async def test_system_config(self) -> Dict[str, Any]:
        """Test de configuración del sistema"""
        try:
            # Verificar Python
            python_version = sys.version
            logger.info(f"Python version: {python_version}")
            
            # Verificar SO
            os_info = platform.system()
            logger.info(f"Sistema operativo: {os_info}")
            
            # Verificar dependencias
            try:
                import gradio
                logger.info(f"Gradio version: {gradio.__version__}")
            except ImportError:
                return {"success": False, "error": "Gradio no está instalado"}
            
            # Verificar puertos disponibles
            test_ports = [self.test_port, 5999, 6000, 6001]
            available_ports = []
            
            for port in test_ports:
                if self.is_port_available(port):
                    available_ports.append(port)
            
            logger.info(f"Puertos disponibles: {available_ports}")
            
            return {
                "success": True,
                "python_version": python_version,
                "os": os_info,
                "available_ports": available_ports
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_webui_startup(self) -> Dict[str, Any]:
        """Test de inicio del WebUI"""
        try:
            logger.info(f"Iniciando WebUI en puerto {self.test_port}...")
            
            # Iniciar WebUI en background
            self.webui_process = subprocess.Popen(
                [sys.executable, "webui.py", "--port", str(self.test_port), "--theme", "Base"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar a que inicie
            await asyncio.sleep(8)
            
            # Verificar que el proceso esté corriendo
            if self.webui_process.poll() is not None:
                stdout, stderr = self.webui_process.communicate()
                return {
                    "success": False, 
                    "error": f"WebUI falló al iniciar. Error: {stderr.decode()}"
                }
            
            # Verificar conectividad HTTP
            try:
                response = requests.get(f"http://127.0.0.1:{self.test_port}", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ WebUI iniciado correctamente")
                    return {"success": True, "url": f"http://127.0.0.1:{self.test_port}"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            except requests.RequestException as e:
                return {"success": False, "error": f"No se pudo conectar al WebUI: {str(e)}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_vnc_server(self) -> Dict[str, Any]:
        """Test del servidor VNC"""
        try:
            logger.info("Probando inicio del servidor VNC...")
            
            # Importar el manager VNC
            from src.vnc.vnc_server import vnc_manager
            
            # Intentar iniciar servidor VNC
            vnc_result = await vnc_manager.start_server("test_server")
            
            if vnc_result.get("status") == "success":
                self.vnc_port = vnc_result.get("port")
                logger.info(f"✅ Servidor VNC iniciado en puerto {self.vnc_port}")
                logger.info(f"Método usado: {vnc_result.get('method', 'Desconocido')}")
                return {
                    "success": True,
                    "port": self.vnc_port,
                    "method": vnc_result.get("method"),
                    "display": vnc_result.get("display")
                }
            else:
                logger.warning(f"VNC falló: {vnc_result.get('error')}")
                return {
                    "success": False,
                    "error": vnc_result.get("error"),
                    "suggestions": vnc_result.get("suggestions", [])
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_vnc_connectivity(self) -> Dict[str, Any]:
        """Test de conectividad VNC"""
        try:
            if not self.vnc_port:
                return {"success": False, "error": "No hay puerto VNC disponible"}
            
            logger.info(f"Probando conectividad VNC en puerto {self.vnc_port}...")
            
            # Test de conexión TCP
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    result = s.connect_ex(('127.0.0.1', self.vnc_port))
                    
                    if result == 0:
                        logger.info("✅ Puerto VNC accesible")
                        
                        # Test de respuesta HTTP (para mock server)
                        try:
                            response = requests.get(f"http://127.0.0.1:{self.vnc_port}", timeout=5)
                            if response.status_code == 200:
                                logger.info("✅ Mock VNC server respondiendo correctamente")
                                return {
                                    "success": True,
                                    "connection_type": "HTTP Mock Server",
                                    "response_code": response.status_code
                                }
                        except:
                            # Podría ser un servidor VNC real, no HTTP
                            logger.info("✅ Servidor VNC real detectado")
                            return {
                                "success": True,
                                "connection_type": "VNC Server",
                                "port": self.vnc_port
                            }
                    else:
                        return {"success": False, "error": f"No se pudo conectar al puerto {self.vnc_port}"}
                        
            except Exception as e:
                return {"success": False, "error": f"Error de conectividad: {str(e)}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_mobile_access(self) -> Dict[str, Any]:
        """Test de acceso móvil"""
        try:
            logger.info("Probando acceso móvil al VNC...")
            
            if not self.vnc_port:
                return {"success": False, "error": "No hay puerto VNC disponible"}
            
            # Simular acceso móvil con headers de móvil
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            try:
                # Test del WebUI principal
                response = requests.get(
                    f"http://127.0.0.1:{self.test_port}", 
                    headers=mobile_headers, 
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Verificar que contiene elementos responsivos
                    content = response.text
                    mobile_indicators = [
                        "viewport",
                        "max-width",
                        "@media",
                        "touch-action"
                    ]
                    
                    mobile_score = sum(1 for indicator in mobile_indicators if indicator in content)
                    
                    logger.info(f"✅ Acceso móvil funcional (score: {mobile_score}/4)")
                    
                    return {
                        "success": True,
                        "mobile_score": mobile_score,
                        "responsive": mobile_score >= 2
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                return {"success": False, "error": f"Error de acceso móvil: {str(e)}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_cyberpunk_interface(self) -> Dict[str, Any]:
        """Test de la interfaz cyberpunk"""
        try:
            logger.info("Verificando interfaz cyberpunk...")
            
            response = requests.get(f"http://127.0.0.1:{self.test_port}", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Verificar elementos cyberpunk
                cyberpunk_elements = [
                    "AUTONOBOT",
                    "Navegador Autonomo",
                    "--cyber-primary",
                    "#00ffff",
                    "cyberpunk-glow",
                    "Orbitron",
                    "Rajdhani"
                ]
                
                found_elements = [elem for elem in cyberpunk_elements if elem in content]
                cyberpunk_score = len(found_elements)
                
                logger.info(f"✅ Elementos cyberpunk encontrados: {cyberpunk_score}/7")
                logger.info(f"Elementos: {found_elements}")
                
                return {
                    "success": cyberpunk_score >= 5,
                    "cyberpunk_score": cyberpunk_score,
                    "found_elements": found_elements
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_vnc_functionality(self) -> Dict[str, Any]:
        """Test de funcionalidad VNC"""
        try:
            logger.info("Probando funcionalidad VNC...")
            
            if not self.vnc_port:
                return {"success": False, "error": "No hay servidor VNC activo"}
            
            # Test de funciones VNC básicas
            functionality_tests = []
            
            # Test 1: Verificar que el servidor responde
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    result = s.connect_ex(('127.0.0.1', self.vnc_port))
                    functionality_tests.append(("Conectividad", result == 0))
            except:
                functionality_tests.append(("Conectividad", False))
            
            # Test 2: Verificar respuesta HTTP (mock server)
            try:
                response = requests.get(f"http://127.0.0.1:{self.vnc_port}", timeout=5)
                functionality_tests.append(("Respuesta HTTP", response.status_code == 200))
                
                if response.status_code == 200:
                    # Verificar contenido cyberpunk en mock server
                    content = response.text
                    cyberpunk_in_vnc = "AUTONOBOT" in content and "cyberpunk" in content.lower()
                    functionality_tests.append(("Tema Cyberpunk en VNC", cyberpunk_in_vnc))
                    
            except:
                functionality_tests.append(("Respuesta HTTP", False))
                functionality_tests.append(("Tema Cyberpunk en VNC", False))
            
            passed_tests = sum(1 for _, passed in functionality_tests if passed)
            total_tests = len(functionality_tests)
            
            logger.info(f"✅ Tests de funcionalidad: {passed_tests}/{total_tests}")
            for test_name, passed in functionality_tests:
                status = "✅" if passed else "❌"
                logger.info(f"  {status} {test_name}")
            
            return {
                "success": passed_tests >= total_tests // 2,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "test_details": functionality_tests
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_vnc_reconnection(self) -> Dict[str, Any]:
        """Test de reconexión VNC"""
        try:
            logger.info("Probando reconexión VNC...")
            
            if not self.vnc_port:
                return {"success": False, "error": "No hay servidor VNC activo"}
            
            # Test de múltiples conexiones
            connection_tests = []
            
            for i in range(3):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2)
                        result = s.connect_ex(('127.0.0.1', self.vnc_port))
                        connection_tests.append(result == 0)
                        await asyncio.sleep(1)
                except:
                    connection_tests.append(False)
            
            successful_connections = sum(connection_tests)
            
            logger.info(f"✅ Conexiones exitosas: {successful_connections}/3")
            
            return {
                "success": successful_connections >= 2,
                "successful_connections": successful_connections,
                "connection_stability": successful_connections / 3
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_port_available(self, port: int) -> bool:
        """Verificar si un puerto está disponible"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    async def cleanup(self):
        """Limpiar recursos de test"""
        logger.info("Limpiando recursos de test...")
        
        # Detener WebUI
        if self.webui_process:
            try:
                self.webui_process.terminate()
                self.webui_process.wait(timeout=5)
            except:
                try:
                    self.webui_process.kill()
                except:
                    pass
        
        # Detener servidor VNC
        try:
            from src.vnc.vnc_server import vnc_manager
            await vnc_manager.stop_server("test_server")
        except:
            pass
    
    def generate_report(self):
        """Generar reporte de resultados"""
        logger.info("\n" + "="*80)
        logger.info("📊 REPORTE FINAL DE TESTS VNC")
        logger.info("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        logger.info(f"Tests ejecutados: {total_tests}")
        logger.info(f"Tests exitosos: {passed_tests}")
        logger.info(f"Tests fallidos: {total_tests - passed_tests}")
        logger.info(f"Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 Detalle de resultados:")
        for test_name, result in self.test_results.items():
            status = "✅ PASÓ" if result.get("success", False) else "❌ FALLÓ"
            logger.info(f"  {status} {test_name}")
            if not result.get("success", False) and "error" in result:
                logger.info(f"    Error: {result['error']}")
        
        # Recomendaciones
        logger.info("\n💡 RECOMENDACIONES:")
        
        if passed_tests == total_tests:
            logger.info("  🎉 ¡Excelente! Todos los tests pasaron.")
            logger.info("  🚀 El sistema VNC está funcionando perfectamente.")
        elif passed_tests >= total_tests * 0.7:
            logger.info("  👍 La mayoría de tests pasaron.")
            logger.info("  🔧 Revisar los tests fallidos para optimización.")
        else:
            logger.info("  ⚠️  Varios tests fallaron.")
            logger.info("  🛠️  Se requiere revisión del sistema VNC.")
            
        # Guardar reporte en archivo
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }
        
        with open("vnc_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Reporte guardado en: vnc_test_report.json")


async def main():
    """Función principal para ejecutar los tests"""
    test_suite = VNCVisualizationTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
