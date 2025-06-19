#!/usr/bin/env python3
"""
Test visual interactivo para evaluar la visualización del VNC en AUTONOBOT
Este script abre automáticamente las ventanas necesarias para evaluación visual
"""

import asyncio
import logging
import subprocess
import sys
import time
import webbrowser
import platform
from typing import Dict, Any
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VNCVisualInteractiveTest:
    """Test visual interactivo para VNC"""
    
    def __init__(self):
        self.webui_process = None
        self.test_port = 7791
        self.vnc_port = None
        
    async def run_interactive_test(self):
        """Ejecutar test visual interactivo"""
        logger.info("🎨 Iniciando test visual interactivo de VNC")
        logger.info("="*60)
        
        try:
            # Paso 1: Iniciar WebUI
            await self.start_webui()
            
            # Paso 2: Abrir navegador automáticamente
            await self.open_browser_windows()
            
            # Paso 3: Guía interactiva
            await self.interactive_guide()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Test interrumpido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error en test interactivo: {e}")
        finally:
            await self.cleanup()
    
    async def start_webui(self):
        """Iniciar WebUI para test"""
        logger.info(f"🚀 Iniciando AUTONOBOT WebUI en puerto {self.test_port}...")
        
        # Iniciar WebUI
        self.webui_process = subprocess.Popen(
            [sys.executable, "webui.py", "--port", str(self.test_port), "--theme", "Base"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar a que inicie
        logger.info("⏳ Esperando que el WebUI inicie...")
        await asyncio.sleep(10)
        
        # Verificar que esté corriendo
        if self.webui_process.poll() is not None:
            stdout, stderr = self.webui_process.communicate()
            raise Exception(f"WebUI falló al iniciar: {stderr.decode()}")
        
        logger.info("✅ WebUI iniciado correctamente")
    
    async def open_browser_windows(self):
        """Abrir ventanas del navegador automáticamente"""
        logger.info("🌐 Abriendo ventanas del navegador para evaluación visual...")
        
        urls_to_open = [
            {
                "url": f"http://127.0.0.1:{self.test_port}",
                "description": "Interfaz principal de AUTONOBOT"
            },
            {
                "url": f"http://127.0.0.1:{self.test_port}?__theme=dark",
                "description": "Interfaz con tema oscuro forzado"
            }
        ]
        
        for i, url_info in enumerate(urls_to_open):
            logger.info(f"📱 Abriendo: {url_info['description']}")
            try:
                webbrowser.open(url_info["url"])
                await asyncio.sleep(2)  # Esperar entre aperturas
            except Exception as e:
                logger.warning(f"⚠️ No se pudo abrir automáticamente: {e}")
                logger.info(f"🔗 Abrir manualmente: {url_info['url']}")
    
    async def interactive_guide(self):
        """Guía interactiva para evaluación visual"""
        logger.info("\n" + "="*60)
        logger.info("🎯 GUÍA DE EVALUACIÓN VISUAL VNC")
        logger.info("="*60)
        
        # Lista de verificaciones visuales
        visual_checks = [
            {
                "step": 1,
                "title": "Verificar Interfaz Cyberpunk",
                "description": "¿Se ve la interfaz con tema cyberpunk (colores neón, efectos de brillo)?",
                "details": [
                    "- Título: 'AUTONOBOT - Navegador Autónomo'",
                    "- Colores neón: cyan (#00ffff), magenta (#ff00ff), verde (#00ff41)",
                    "- Efectos de brillo en bordes y texto",
                    "- Fondo oscuro con gradientes"
                ]
            },
            {
                "step": 2,
                "title": "Verificar Localización en Español",
                "description": "¿Están todos los textos en español?",
                "details": [
                    "- Tabs: 'Configuración de Agente', 'Agente Interactivo', etc.",
                    "- Botones y etiquetas en español",
                    "- Mensajes de estado en español"
                ]
            },
            {
                "step": 3,
                "title": "Probar Modo VNC",
                "description": "¿Funciona el cambio a modo VNC?",
                "details": [
                    "- Ir a tab 'Agente Interactivo'",
                    "- Cambiar de 'Navegador Local' a 'Visor Remoto VNC'",
                    "- Verificar que aparece botón 'Activar Visor VNC'",
                    "- Hacer clic en 'Activar Visor VNC'"
                ]
            },
            {
                "step": 4,
                "title": "Verificar Visor VNC",
                "description": "¿Se abre correctamente el visor VNC?",
                "details": [
                    "- Se abre nueva ventana/modal con visor VNC",
                    "- Título: 'AUTONOBOT - Visor Remoto'",
                    "- Interfaz cyberpunk en el visor",
                    "- Botones: 'Pantalla Completa', 'Reconectar', 'Cerrar'"
                ]
            },
            {
                "step": 5,
                "title": "Verificar Responsividad Móvil",
                "description": "¿Se adapta la interfaz en móvil?",
                "details": [
                    "- Abrir herramientas de desarrollador (F12)",
                    "- Activar modo móvil/responsive",
                    "- Verificar que la interfaz se adapta",
                    "- Botones táctiles de tamaño adecuado"
                ]
            },
            {
                "step": 6,
                "title": "Verificar Animaciones",
                "description": "¿Funcionan las animaciones cyberpunk?",
                "details": [
                    "- Efectos de hover en botones",
                    "- Animaciones de brillo en texto",
                    "- Transiciones suaves",
                    "- Efectos de escaneo en VNC viewer"
                ]
            }
        ]
        
        results = {}
        
        for check in visual_checks:
            logger.info(f"\n📋 PASO {check['step']}: {check['title']}")
            logger.info("-" * 50)
            logger.info(f"🎯 {check['description']}")
            logger.info("\n📝 Detalles a verificar:")
            for detail in check['details']:
                logger.info(f"  {detail}")
            
            # Esperar input del usuario
            while True:
                try:
                    response = input(f"\n✅ ¿Paso {check['step']} completado correctamente? (s/n/ayuda): ").lower().strip()
                    
                    if response in ['s', 'si', 'sí', 'y', 'yes']:
                        results[f"step_{check['step']}"] = {"passed": True, "title": check['title']}
                        logger.info(f"✅ Paso {check['step']} marcado como exitoso")
                        break
                    elif response in ['n', 'no']:
                        issue = input("❓ Describe el problema encontrado: ").strip()
                        results[f"step_{check['step']}"] = {
                            "passed": False, 
                            "title": check['title'],
                            "issue": issue
                        }
                        logger.info(f"❌ Paso {check['step']} marcado como fallido")
                        break
                    elif response in ['ayuda', 'help', 'h']:
                        await self.show_help(check['step'])
                    else:
                        logger.info("❓ Respuesta no válida. Usa: s/n/ayuda")
                        
                except KeyboardInterrupt:
                    logger.info("\n⚠️ Test interrumpido")
                    return results
        
        # Generar reporte final
        await self.generate_visual_report(results)
        return results
    
    async def show_help(self, step: int):
        """Mostrar ayuda específica para cada paso"""
        help_info = {
            1: {
                "title": "Ayuda: Verificar Interfaz Cyberpunk",
                "tips": [
                    "🔍 Busca colores brillantes (cyan, magenta, verde neón)",
                    "🌟 Los bordes deben tener efectos de brillo",
                    "🎨 El fondo debe ser oscuro con gradientes",
                    "📝 El título debe decir 'AUTONOBOT - Navegador Autónomo'",
                    "⚡ Si no ves efectos cyberpunk, verifica que el CSS se cargó"
                ]
            },
            2: {
                "title": "Ayuda: Verificar Localización",
                "tips": [
                    "🇪🇸 Todos los textos deben estar en español",
                    "📑 Revisa los nombres de las pestañas",
                    "🔘 Verifica etiquetas de botones y campos",
                    "💬 Los mensajes de estado deben estar en español",
                    "⚠️ Si ves texto en inglés, reporta dónde"
                ]
            },
            3: {
                "title": "Ayuda: Probar Modo VNC",
                "tips": [
                    "🖱️ Ve a la pestaña 'Agente Interactivo'",
                    "🔄 Busca el selector 'Modo de Visualización'",
                    "📺 Cambia a 'Visor Remoto VNC'",
                    "🚀 Debe aparecer botón 'Activar Visor VNC'",
                    "⚡ Si no aparece, verifica la configuración VNC"
                ]
            },
            4: {
                "title": "Ayuda: Verificar Visor VNC",
                "tips": [
                    "🖥️ Debe abrirse una nueva ventana o modal",
                    "🎨 La interfaz del visor debe tener tema cyberpunk",
                    "🔧 Verifica que los botones funcionen",
                    "📱 Prueba en modo pantalla completa",
                    "🔄 Prueba el botón de reconexión"
                ]
            },
            5: {
                "title": "Ayuda: Verificar Responsividad",
                "tips": [
                    "🔧 Abre DevTools (F12)",
                    "📱 Activa modo responsive/móvil",
                    "📏 Cambia el tamaño de pantalla",
                    "👆 Verifica que los botones sean táctiles",
                    "🎨 La interfaz debe adaptarse sin romperse"
                ]
            },
            6: {
                "title": "Ayuda: Verificar Animaciones",
                "tips": [
                    "🖱️ Pasa el mouse sobre botones y elementos",
                    "✨ Debe haber efectos de brillo y hover",
                    "🔄 Las transiciones deben ser suaves",
                    "⚡ El texto del título debe tener animación",
                    "🎭 En el VNC viewer debe haber efecto de escaneo"
                ]
            }
        }
        
        if step in help_info:
            info = help_info[step]
            logger.info(f"\n💡 {info['title']}")
            logger.info("-" * 40)
            for tip in info['tips']:
                logger.info(f"  {tip}")
        else:
            logger.info("❓ No hay ayuda específica para este paso")
    
    async def generate_visual_report(self, results: Dict[str, Any]):
        """Generar reporte de evaluación visual"""
        logger.info("\n" + "="*60)
        logger.info("📊 REPORTE DE EVALUACIÓN VISUAL")
        logger.info("="*60)
        
        total_steps = len(results)
        passed_steps = sum(1 for result in results.values() if result.get("passed", False))
        
        logger.info(f"📈 Pasos evaluados: {total_steps}")
        logger.info(f"✅ Pasos exitosos: {passed_steps}")
        logger.info(f"❌ Pasos fallidos: {total_steps - passed_steps}")
        logger.info(f"🎯 Porcentaje de éxito: {(passed_steps/total_steps)*100:.1f}%")
        
        logger.info("\n📋 Detalle por paso:")
        for step_key, result in results.items():
            status = "✅" if result.get("passed", False) else "❌"
            logger.info(f"  {status} {result['title']}")
            if not result.get("passed", False) and "issue" in result:
                logger.info(f"    🐛 Problema: {result['issue']}")
        
        # Recomendaciones
        logger.info("\n💡 RECOMENDACIONES:")
        if passed_steps == total_steps:
            logger.info("  🎉 ¡Perfecto! La visualización VNC funciona excelentemente")
            logger.info("  🚀 El sistema está listo para uso en producción")
        elif passed_steps >= total_steps * 0.8:
            logger.info("  👍 La visualización funciona bien con problemas menores")
            logger.info("  🔧 Revisar los problemas reportados para optimización")
        else:
            logger.info("  ⚠️ Se encontraron varios problemas de visualización")
            logger.info("  🛠️ Se requiere revisión y corrección antes de usar")
        
        # Guardar reporte
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "Visual Interactive Test",
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "success_rate": (passed_steps/total_steps)*100,
            "results": results,
            "system_info": {
                "platform": platform.system(),
                "python_version": sys.version
            }
        }
        
        with open("vnc_visual_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Reporte visual guardado en: vnc_visual_test_report.json")
    
    async def cleanup(self):
        """Limpiar recursos"""
        logger.info("\n🧹 Limpiando recursos...")
        
        if self.webui_process:
            try:
                self.webui_process.terminate()
                self.webui_process.wait(timeout=5)
                logger.info("✅ WebUI detenido")
            except:
                try:
                    self.webui_process.kill()
                    logger.info("⚡ WebUI forzado a cerrar")
                except:
                    logger.warning("⚠️ No se pudo detener WebUI completamente")


async def main():
    """Función principal"""
    logger.info("🎨 AUTONOBOT - Test Visual Interactivo de VNC")
    logger.info("="*50)
    logger.info("Este test te guiará para evaluar visualmente el sistema VNC")
    logger.info("Se abrirán ventanas automáticamente para la evaluación")
    logger.info("="*50)
    
    input("📱 Presiona Enter para comenzar el test visual...")
    
    test_suite = VNCVisualInteractiveTest()
    await test_suite.run_interactive_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
