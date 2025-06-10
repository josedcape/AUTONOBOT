@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    AUTONOBOT Installation Script
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

:: Check Python version (basic check for 3.11+)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo ERROR: Python version %PYTHON_VERSION% is too old
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    echo ERROR: Python version %PYTHON_VERSION% is too old
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

echo ✓ Python version check passed

:: Create necessary directories
echo.
echo Creating directories...
if not exist "tmp" mkdir tmp
if not exist "tmp\record_videos" mkdir tmp\record_videos
if not exist "tmp\traces" mkdir tmp\traces
if not exist "tmp\agent_history" mkdir tmp\agent_history
echo ✓ Directories created

:: Install dependencies
echo.
echo Installing Python dependencies...
echo This may take a few minutes...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo ✓ Dependencies installed

:: Install Playwright browsers
echo.
echo Installing Playwright browsers...
echo This may take several minutes...
python -m playwright install
if errorlevel 1 (
    echo WARNING: Playwright browser installation failed
    echo You may need to install browsers manually later
) else (
    echo ✓ Playwright browsers installed
)

:: Setup environment file
echo.
echo Setting up environment configuration...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    if errorlevel 1 (
        echo ERROR: Failed to create .env file
        pause
        exit /b 1
    )
    echo ✓ Environment file created from template
) else (
    echo ✓ Environment file already exists
)

:: Create launcher script
echo.
echo Creating launcher script...
(
echo @echo off
echo echo Starting AUTONOBOT Browser Use Web UI...
echo echo.
echo echo Web UI will be available at: http://127.0.0.1:7788
echo echo.
echo python webui.py --auto-open
echo pause
) > start_autonobot.bat
echo ✓ Launcher script created

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file to add your API keys for LLM providers
echo 2. Run start_autonobot.bat to launch the application
echo 3. Or run: python webui.py
echo.
echo The web interface will be available at:
echo http://127.0.0.1:7788
echo.
echo For help and documentation, visit:
echo https://github.com/browser-use/web-ui
echo.
pause
