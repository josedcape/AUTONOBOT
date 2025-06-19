# 🤖 AUTONOBOT
## Navegador Autónomo Avanzado

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Mobile](https://img.shields.io/badge/Mobile-Compatible-brightgreen.svg)](https://github.com)
[![VNC](https://img.shields.io/badge/VNC-Enabled-orange.svg)](https://github.com)
[![Cyberpunk](https://img.shields.io/badge/Theme-Cyberpunk-ff00ff.svg)](https://github.com)

> **Sistema de navegación web inteligente con IA avanzada y interfaz cyberpunk futurista**

AUTONOBOT es un sistema de automatización de navegador web de última generación que combina inteligencia artificial avanzada con una interfaz cyberpunk visualmente impactante. Diseñado para automatización web profesional, investigación, y control remoto desde dispositivos móviles.

![AUTONOBOT Cyberpunk Interface](assets/autonobot-cyberpunk-preview.png)

---

## 📋 Tabla de Contenidos

- [🌟 Características Principales](#-características-principales)
- [📱 Optimización Móvil](#-optimización-móvil)
- [🚀 Instalación Rápida](#-instalación-rápida)
- [💻 Instalación Detallada](#-instalación-detallada)
- [🎮 Uso de la Aplicación](#-uso-de-la-aplicación)
- [📺 Configuración VNC](#-configuración-vnc)
- [🧪 Testing y Verificación](#-testing-y-verificación)
- [🛠️ Solución de Problemas](#️-solución-de-problemas)
- [🤝 Contribuir](#-contribuir)
- [📄 Licencia](#-licencia)

---

## 🌟 Características Principales

### 🎨 **Interfaz Cyberpunk Futurista**
- **Tema Visual Cyberpunk**: Colores neón (cyan #00ffff, magenta #ff00ff, verde #00ff41)
- **Animaciones Avanzadas**: Efectos de pulso, escaneo y transiciones suaves
- **Tipografía Futurista**: Fuentes Orbitron y Rajdhani optimizadas para máxima legibilidad
- **Efectos de Brillo**: Bordes y texto con efectos glow dinámicos
- **Diseño Responsivo**: Adaptación perfecta a dispositivos móviles y desktop

### 🇪🇸 **Interfaz Completamente en Español**
- **Localización Completa**: Todos los textos y mensajes en español
- **Navegación Intuitiva**: Pestañas y controles localizados
- **Mensajes de Estado**: Retroalimentación en tiempo real en español
- **Codificación Segura**: Sin problemas de caracteres especiales

### 🤖 **Automatización IA Avanzada**
- **Control Inteligente**: Navegación web automatizada con IA
- **Chat Interactivo**: Comunicación en tiempo real con el agente
- **Soporte Multi-tarea**: Gestión simultánea de múltiples procesos
- **Control en Tiempo Real**: Monitoreo y ajuste dinámico de tareas
- **Configuración Flexible**: Múltiples modelos de IA soportados

### 📱 **Acceso Móvil Completo**
- **VNC Viewer Integrado**: Visualización remota desde móviles
- **Controles Táctiles**: Botones optimizados para dispositivos touch
- **Interfaz Responsiva**: Adaptación automática a pantallas pequeñas
- **Acceso Universal**: Compatible con iOS, Android y tablets
- **Botones Flotantes**: FABs para acceso rápido en móvil

### 🖥️ **Modos de Visualización Duales**
- **Modo PC Local**: Navegador se abre en tu computadora
- **Modo VNC Remoto**: Visualización a través de VNC viewer
- **Cambio Dinámico**: Alternancia sin reiniciar la aplicación
- **Compatibilidad Multiplataforma**: Windows, Linux, macOS

---

## 📱 Optimización Móvil

### 🎯 **Controles Táctiles Mejorados**

AUTONOBOT incluye optimizaciones específicas para dispositivos móviles:

#### **Botones de Acción Flotantes (FABs)**
- **Acceso Rápido**: Botones flotantes para funciones principales
- **Posicionamiento Inteligente**: Ubicación óptima para uso con pulgar
- **Feedback Táctil**: Respuesta visual inmediata al toque
- **Tamaño Optimizado**: Mínimo 44px para accesibilidad táctil

#### **VNC Viewer Móvil**
- **Controles Touch**: Gestos nativos para zoom, pan y navegación
- **Barra de Herramientas Móvil**: Controles adaptados para pantallas pequeñas
- **Modo Pantalla Completa**: Experiencia inmersiva en móvil
- **Reconexión Automática**: Manejo inteligente de conexiones móviles

### 📲 **Acceso desde Dispositivos Móviles**

#### **Configuración Rápida**
1. **Conecta tu móvil a la misma red WiFi** que tu PC
2. **Obtén la IP de tu PC**:
   - Windows: `ipconfig`
   - Linux/Mac: `ifconfig`
   - O usa: `python -c "import socket; print(socket.gethostbyname(socket.gethostname()))"`
3. **Abre en tu móvil**: `http://[IP-DE-TU-PC]:7788`
4. **Disfruta de la interfaz cyberpunk** optimizada para móvil

#### **Compatibilidad Móvil**
- ✅ **iOS Safari** (iPhone/iPad)
- ✅ **Android Chrome** (Teléfonos/Tablets)
- ✅ **Samsung Internet**
- ✅ **Firefox Mobile**
- ✅ **Edge Mobile**

---

## 🚀 Instalación Rápida

### 📋 **Requisitos Previos**
- **Python 3.8+** (Recomendado: Python 3.10+)
- **Git** para clonar el repositorio
- **Navegador web moderno** (Chrome, Firefox, Safari, Edge)
- **4GB RAM mínimo** (8GB recomendado)
- **Conexión a internet** para descargar dependencias

### ⚡ **Instalación en 3 Pasos**

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. ¡Ejecutar AUTONOBOT!
python webui.py
```

**¡Listo!** Abre tu navegador en `http://localhost:7788` y disfruta de la experiencia cyberpunk.

### 🎯 **Verificación Rápida**

```bash
# Ejecutar test rápido para verificar instalación
python test_vnc_quick.py
```

---

## 💻 Instalación Detallada

### 🪟 **Windows**

#### **Opción 1: Instalación Estándar**
```cmd
# 1. Instalar Python 3.10+ desde python.org
# 2. Abrir PowerShell como administrador
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot
pip install -r requirements.txt

# 3. Configurar VNC (opcional para acceso móvil)
python setup_windows_vnc.py

# 4. Ejecutar
python webui.py
```

#### **Opción 2: Con Anaconda**
```cmd
# 1. Instalar Anaconda
conda create -n autonobot python=3.10
conda activate autonobot
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot
pip install -r requirements.txt
python webui.py
```

### 🐧 **Linux (Ubuntu/Debian)**

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias del sistema
sudo apt install python3 python3-pip git xvfb x11vnc -y

# 3. Clonar e instalar
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot
pip3 install -r requirements.txt

# 4. Configurar VNC
sudo apt install tightvncserver -y

# 5. Ejecutar
python3 webui.py
```

### 🍎 **macOS**

```bash
# 1. Instalar Homebrew (si no está instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar dependencias
brew install python git

# 3. Clonar e instalar
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot
pip3 install -r requirements.txt

# 4. Instalar VNC (opcional)
brew install x11vnc

# 5. Ejecutar
python3 webui.py
```

### 🐳 **Docker (Multiplataforma)**

```bash
# 1. Construir imagen
docker build -t autonobot .

# 2. Ejecutar contenedor
docker run -p 7788:7788 -p 5999:5999 autonobot

# 3. Acceder
# Navegador: http://localhost:7788
# VNC: localhost:5999
```

---

## 🎮 Uso de la Aplicación

### 🚀 **Inicio Rápido**

1. **Ejecutar AUTONOBOT**:
   ```bash
   python webui.py
   ```

2. **Abrir navegador** en `http://localhost:7788`

3. **Configurar tu primer agente**:
   - Ve a "🔧 Configuración de Agente"
   - Selecciona tu modelo de IA preferido
   - Configura las credenciales API

4. **¡Comenzar a automatizar!**:
   - Ve a "🤖 Agente Interactivo"
   - Escribe tu tarea en el chat
   - Observa cómo AUTONOBOT navega automáticamente

### 🎛️ **Opciones de Línea de Comandos**

```bash
# Puerto personalizado
python webui.py --port 8080

# Tema específico
python webui.py --theme Base

# IP específica (para acceso remoto)
python webui.py --ip 0.0.0.0 --port 7788

# Ayuda completa
python webui.py --help
```

### 📊 **Pestañas de la Interfaz**

1. **🔧 Configuración de Agente**: Configurar modelos de IA y parámetros
2. **🌐 Configuración del Navegador**: Ajustes del navegador y automatización
3. **🤖 Agente Interactivo**: Chat en tiempo real con el agente IA
4. **📊 Cola de Tareas**: Monitoreo de tareas en progreso
5. **💾 Resultados**: Historial y análisis de resultados
6. **🎛️ Grabaciones**: Sesiones guardadas y reproducciones
7. **⚙️ Configuración**: Guardar/cargar configuraciones

---

## 📺 Configuración VNC

### 🎯 **¿Qué es VNC y por qué usarlo?**

VNC (Virtual Network Computing) permite ver y controlar AUTONOBOT desde dispositivos móviles o remotos. Perfecto para:
- **Monitoreo móvil**: Ver automatización desde tu teléfono
- **Acceso remoto**: Controlar desde cualquier lugar
- **Demostraciones**: Mostrar AUTONOBOT en presentaciones
- **Debugging**: Observar el comportamiento del agente

### 🔧 **Configuración por Plataforma**

#### **Windows**
```cmd
# Opción 1: Configuración automática
python setup_windows_vnc.py

# Opción 2: WSL (Windows Subsystem for Linux)
wsl --install
# Luego seguir instrucciones de Linux

# Opción 3: Docker Desktop
# Instalar Docker Desktop y usar contenedor
```

#### **Linux**
```bash
# Ubuntu/Debian
sudo apt install xvfb x11vnc tightvncserver -y

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb x11vnc tigervnc-server -y

# Arch Linux
sudo pacman -S xorg-server-xvfb x11vnc tigervnc -y
```

#### **macOS**
```bash
# Con Homebrew
brew install x11vnc

# Configurar permisos de accesibilidad
# Sistema > Privacidad > Accesibilidad > Permitir x11vnc
```

### 📱 **Uso de VNC**

1. **Cambiar a modo VNC**:
   - Ve a "🤖 Agente Interactivo"
   - Selecciona "📺 Visor Remoto VNC"
   - Haz clic en "🚀 Activar Visor VNC"

2. **Acceso desde móvil**:
   - Abre `http://[IP-DE-TU-PC]:7788` en tu móvil
   - La interfaz se adaptará automáticamente
   - Usa los controles táctiles optimizados

3. **Controles VNC**:
   - **⛶ Pantalla Completa**: Modo inmersivo
   - **🔄 Reconectar**: Restablecer conexión
   - **✕ Cerrar**: Salir del visor

---

## 🧪 Testing y Verificación

AUTONOBOT incluye un sistema completo de testing para verificar que todo funcione correctamente:

### ⚡ **Test Rápido**
```bash
python test_vnc_quick.py
```
- Verificación automática en 2-3 minutos
- Abre navegador automáticamente
- Verifica interfaz cyberpunk y VNC

### 🔍 **Test Completo**
```bash
python test_vnc_visualization.py
```
- Test exhaustivo con reporte JSON
- Incluye verificación móvil
- Análisis detallado de rendimiento

### 👀 **Test Visual Interactivo**
```bash
python test_vnc_visual_interactive.py
```
- Guía paso a paso para evaluación manual
- Verificación de experiencia de usuario
- Feedback interactivo

### 📋 **Test Manual**
```bash
python test_vnc_manual.py
```
- Guía rápida de verificación
- Lista de comprobación visual
- Detección automática de WebUI

### 📊 **Interpretación de Resultados**

- **🎉 80-100%**: Sistema listo para producción
- **👍 60-79%**: Funcional con mejoras menores
- **⚠️ <60%**: Requiere corrección antes de usar

Los tests generan reportes automáticos en formato JSON para análisis detallado.

---

## 🛠️ Solución de Problemas

### ❌ **Problemas Comunes**

#### **Error: Puerto ocupado**
```bash
# Verificar qué proceso usa el puerto
netstat -ano | findstr :7788  # Windows
lsof -i :7788                 # Linux/Mac

# Usar puerto diferente
python webui.py --port 8080
```

#### **Error: VNC no inicia**
```bash
# Windows: Usar mock server (automático)
# Linux: Instalar dependencias VNC
sudo apt install xvfb x11vnc -y

# macOS: Configurar permisos
# Sistema > Privacidad > Accesibilidad
```

#### **Error: Interfaz no cyberpunk**
```bash
# Forzar tema Base
python webui.py --theme Base

# Verificar CSS en navegador (F12)
# Buscar errores en consola
```

#### **Error: No acceso desde móvil**
```bash
# Verificar IP de la PC
ipconfig  # Windows
ifconfig  # Linux/Mac

# Ejecutar con IP específica
python webui.py --ip 0.0.0.0

# Verificar firewall
# Windows: Permitir Python en firewall
# Linux: sudo ufw allow 7788
```

### 🔧 **Debugging Avanzado**

#### **Logs Detallados**
```bash
# Ejecutar con logs verbosos
python webui.py --verbose

# Ver logs en tiempo real
tail -f autonobot.log  # Linux/Mac
Get-Content autonobot.log -Wait  # Windows PowerShell
```

#### **Verificar Dependencias**
```bash
# Verificar instalación
pip list | grep gradio
pip list | grep browser-use

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

#### **Reset Completo**
```bash
# Limpiar cache
rm -rf __pycache__ .gradio  # Linux/Mac
rmdir /s __pycache__ .gradio  # Windows

# Reinstalar desde cero
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### 📞 **Obtener Ayuda**

1. **Ejecutar test de diagnóstico**:
   ```bash
   python test_vnc_visualization.py
   ```

2. **Revisar documentación**: `VNC_TESTING_GUIDE.md`

3. **Reportar issue** con:
   - Reporte de test (JSON)
   - Logs de error
   - Información del sistema
   - Pasos para reproducir

---

## 🤝 Contribuir

### 🎯 **Cómo Contribuir**

1. **Fork** el repositorio
2. **Crear rama** para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. **Commit** tus cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. **Push** a la rama: `git push origin feature/nueva-funcionalidad`
5. **Crear Pull Request**

### 📝 **Guías de Contribución**

#### **Código**
- Seguir PEP 8 para Python
- Documentar funciones y clases
- Incluir tests para nuevas funcionalidades
- Mantener compatibilidad con Python 3.8+

#### **Documentación**
- Usar markdown para documentación
- Incluir ejemplos de código
- Mantener README actualizado
- Documentar cambios en CHANGELOG

#### **Testing**
- Ejecutar todos los tests antes de PR
- Agregar tests para nuevas funcionalidades
- Verificar compatibilidad móvil
- Probar en múltiples plataformas

### 🏆 **Reconocimientos**

Este proyecto está basado en [browser-use](https://github.com/browser-use/browser-use) y agradecemos a todos los contribuidores del proyecto original.

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

### 🙏 **Agradecimientos**

- **browser-use team** por la base sólida del proyecto
- **Gradio team** por la excelente framework de UI
- **Comunidad open source** por las herramientas y librerías
- **Beta testers** por el feedback valioso

---

## 🚀 **¡Comienza Ahora!**

```bash
git clone https://github.com/tu-usuario/autonobot.git
cd autonobot
pip install -r requirements.txt
python webui.py
```

**Abre tu navegador en `http://localhost:7788` y experimenta el futuro de la automatización web con AUTONOBOT!** 🤖✨

---

<div align="center">

**🤖 AUTONOBOT - Navegador Autónomo Avanzado**

*Construido con ❤️ y tecnología cyberpunk*

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/tu-usuario/autonobot)
[![Documentation](https://img.shields.io/badge/Docs-Complete-blue.svg)](README.md)
[![Support](https://img.shields.io/badge/Support-Available-green.svg)](mailto:support@autonobot.com)

</div>
