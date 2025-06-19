#!/usr/bin/env python3
"""
Test manual simple para verificar VNC
"""

import asyncio
import logging
import webbrowser
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_vnc_manual():
    """Test manual de VNC"""
    logger.info("🎯 AUTONOBOT - Test Manual de VNC")
    logger.info("="*40)
    
    # Paso 1: Verificar que el WebUI esté corriendo
    logger.info("📋 PASO 1: Verificar WebUI")
    logger.info("¿Está el WebUI corriendo en algún puerto?")
    
    ports_to_check = [7793, 7792, 7791, 7790, 7789, 7788]
    
    for port in ports_to_check:
        try:
            import requests
            response = requests.get(f"http://127.0.0.1:{port}", timeout=3)
            if response.status_code == 200:
                logger.info(f"✅ WebUI encontrado en puerto {port}")
                
                # Verificar contenido cyberpunk
                content = response.text
                if "AUTONOBOT" in content and "cyberpunk" in content.lower():
                    logger.info("✅ Interfaz cyberpunk detectada")
                    
                    # Abrir navegador
                    logger.info(f"🌐 Abriendo navegador en puerto {port}...")
                    webbrowser.open(f"http://127.0.0.1:{port}")
                    
                    # Guía manual
                    await manual_guide(port)
                    return
                else:
                    logger.warning("⚠️ WebUI encontrado pero sin tema cyberpunk")
        except:
            continue
    
    logger.error("❌ No se encontró WebUI corriendo")
    logger.info("💡 Inicia el WebUI manualmente:")
    logger.info("   python webui.py --port 7792 --theme Base")

async def manual_guide(port: int):
    """Guía manual para test VNC"""
    logger.info("\n" + "="*50)
    logger.info("🎯 GUÍA MANUAL DE VERIFICACIÓN VNC")
    logger.info("="*50)
    
    steps = [
        {
            "step": 1,
            "title": "Verificar Interfaz Cyberpunk",
            "instructions": [
                "🔍 Verifica que veas:",
                "  - Título principal: 'AUTONOBOT'",
                "  - Subtítulo: 'Navegador Autonomo Avanzado'",
                "  - Colores neón (cyan, magenta, verde)",
                "  - Efectos de brillo en bordes",
                "  - Fondo oscuro con gradientes"
            ]
        },
        {
            "step": 2,
            "title": "Verificar Localización Española",
            "instructions": [
                "🇪🇸 Verifica que veas:",
                "  - Pestañas en español",
                "  - 'Configuracion de Agente'",
                "  - 'Agente Interactivo'",
                "  - Todos los textos en español"
            ]
        },
        {
            "step": 3,
            "title": "Probar Funcionalidad VNC",
            "instructions": [
                "🖱️ Sigue estos pasos:",
                "  1. Ve a la pestaña 'Agente Interactivo'",
                "  2. Busca 'Modo de Visualizacion'",
                "  3. Cambia a 'Visor Remoto VNC'",
                "  4. Haz clic en 'Activar Visor VNC'",
                "  5. Verifica que se abra el visor VNC"
            ]
        },
        {
            "step": 4,
            "title": "Verificar Visor VNC",
            "instructions": [
                "📺 En el visor VNC verifica:",
                "  - Título: 'AUTONOBOT'",
                "  - Interfaz cyberpunk",
                "  - Botones: 'Pantalla Completa', 'Reconectar', 'Cerrar'",
                "  - Efectos de animación"
            ]
        },
        {
            "step": 5,
            "title": "Probar Responsividad",
            "instructions": [
                "📱 Prueba responsividad:",
                "  1. Abre DevTools (F12)",
                "  2. Activa modo móvil",
                "  3. Verifica que se adapte la interfaz",
                "  4. Prueba diferentes tamaños de pantalla"
            ]
        }
    ]
    
    results = []
    
    for step_info in steps:
        logger.info(f"\n📋 PASO {step_info['step']}: {step_info['title']}")
        logger.info("-" * 40)
        
        for instruction in step_info['instructions']:
            logger.info(instruction)
        
        # Esperar confirmación del usuario
        while True:
            try:
                response = input(f"\n✅ ¿Paso {step_info['step']} completado exitosamente? (s/n): ").lower().strip()
                
                if response in ['s', 'si', 'sí', 'y', 'yes']:
                    results.append({"step": step_info['step'], "title": step_info['title'], "passed": True})
                    logger.info(f"✅ Paso {step_info['step']} - EXITOSO")
                    break
                elif response in ['n', 'no']:
                    issue = input("❓ Describe el problema: ").strip()
                    results.append({
                        "step": step_info['step'], 
                        "title": step_info['title'], 
                        "passed": False,
                        "issue": issue
                    })
                    logger.info(f"❌ Paso {step_info['step']} - FALLIDO")
                    break
                else:
                    logger.info("❓ Respuesta no válida. Usa 's' para sí o 'n' para no")
            except KeyboardInterrupt:
                logger.info("\n⚠️ Test interrumpido")
                return
    
    # Mostrar resumen
    show_summary(results, port)

def show_summary(results, port):
    """Mostrar resumen del test manual"""
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMEN DEL TEST MANUAL")
    logger.info("="*50)
    
    total_steps = len(results)
    passed_steps = sum(1 for r in results if r.get("passed", False))
    
    logger.info(f"📈 Pasos completados: {passed_steps}/{total_steps}")
    logger.info(f"🎯 Porcentaje de éxito: {(passed_steps/total_steps)*100:.1f}%")
    
    logger.info("\n📋 Detalle por paso:")
    for result in results:
        status = "✅" if result.get("passed", False) else "❌"
        logger.info(f"  {status} Paso {result['step']}: {result['title']}")
        if not result.get("passed", False) and "issue" in result:
            logger.info(f"    🐛 Problema: {result['issue']}")
    
    # Evaluación final
    logger.info("\n💡 EVALUACIÓN FINAL:")
    if passed_steps == total_steps:
        logger.info("🎉 ¡EXCELENTE! Todos los tests pasaron")
        logger.info("🚀 El sistema VNC está funcionando perfectamente")
        logger.info("✅ Listo para uso en producción")
    elif passed_steps >= total_steps * 0.8:
        logger.info("👍 ¡BUENO! La mayoría de tests pasaron")
        logger.info("🔧 Revisar los elementos fallidos para optimización")
        logger.info("⚡ Sistema funcional con mejoras menores pendientes")
    elif passed_steps >= total_steps * 0.6:
        logger.info("⚠️ REGULAR - Funcionalidad básica operativa")
        logger.info("🛠️ Se requieren correcciones para uso óptimo")
        logger.info("📝 Revisar problemas reportados")
    else:
        logger.info("❌ PROBLEMÁTICO - Varios elementos fallaron")
        logger.info("🔧 Se requiere revisión completa del sistema")
        logger.info("🛠️ No recomendado para uso hasta corregir problemas")
    
    # Información adicional
    logger.info(f"\n🌐 URL del WebUI: http://127.0.0.1:{port}")
    logger.info("📱 Para acceso móvil: Reemplaza 127.0.0.1 con la IP de tu PC")
    logger.info("🔧 Para problemas: Revisa VNC_TESTING_GUIDE.md")
    
    # Guardar resultados
    import json
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_type": "Manual VNC Test",
        "port": port,
        "total_steps": total_steps,
        "passed_steps": passed_steps,
        "success_rate": (passed_steps/total_steps)*100,
        "results": results
    }
    
    try:
        with open("vnc_manual_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("📄 Reporte guardado en: vnc_manual_test_report.json")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo guardar reporte: {e}")

async def main():
    """Función principal"""
    print("🎯 AUTONOBOT - Test Manual de Visualización VNC")
    print("=" * 45)
    print("Este test te guiará manualmente para verificar el VNC")
    print("=" * 45)
    
    input("📱 Presiona Enter para comenzar...")
    
    await test_vnc_manual()
    
    print("\n👋 Test manual completado")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
