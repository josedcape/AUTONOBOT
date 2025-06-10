@echo off
echo ========================================
echo    Installing Ollama for Local LLM
echo ========================================
echo.

echo Downloading Ollama installer...
curl -L -o ollama-windows-amd64.exe https://ollama.com/download/OllamaSetup.exe

if exist ollama-windows-amd64.exe (
    echo.
    echo Installing Ollama...
    echo Please follow the installation wizard.
    start /wait ollama-windows-amd64.exe
    
    echo.
    echo Cleaning up...
    del ollama-windows-amd64.exe
    
    echo.
    echo Starting Ollama service...
    ollama serve
) else (
    echo.
    echo Download failed. Please download manually from:
    echo https://ollama.com/download/windows
    echo.
    echo After installation, run: ollama serve
)

pause
