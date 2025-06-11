#!/bin/bash

echo "========================================"
echo "   🛡️ AUTONOBOT - INTERFAZ MEJORADA"
echo "========================================"
echo
echo "Iniciando AUTONOBOT con interfaz futurista..."
echo "Interfaz web estará disponible en: http://127.0.0.1:7788"
echo
echo "Características de la nueva interfaz:"
echo "● Chat Interactivo Listo"
echo "● Soporte Multi-Tarea"  
echo "● Control en Tiempo Real"
echo "● Interfaz completamente en español"
echo "● Diseño futurista con efectos visuales"
echo
echo "Presiona Ctrl+C para detener el servidor"
echo "========================================"
echo

# Determinar comando Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

$PYTHON_CMD webui.py --auto-open

echo
echo "========================================"
echo "AUTONOBOT se ha detenido"
echo "========================================"
