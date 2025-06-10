# AUTONOBOT Installation Guide

## Quick Start (Automated Installation)

### Windows
1. **Download or clone this repository**
2. **Run the installation script:**
   ```cmd
   install.bat
   ```
3. **Start the application:**
   ```cmd
   start_autonobot.bat
   ```

### Linux/macOS
1. **Download or clone this repository**
2. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. **Start the application:**
   ```bash
   ./start_autonobot.sh
   ```

## Prerequisites

- **Python 3.11 or higher** (required)
- **Internet connection** (for downloading dependencies)
- **At least 2GB free disk space** (for browser installations)

### Installing Python

#### Windows
1. Download Python from [python.org](https://python.org)
2. **Important:** Check "Add Python to PATH" during installation
3. Verify installation: Open Command Prompt and run `python --version`

#### macOS
```bash
# Using Homebrew (recommended)
brew install python3

# Or download from python.org
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### CentOS/RHEL/Fedora
```bash
# CentOS/RHEL
sudo yum install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip
```

## Manual Installation

If the automated scripts don't work, follow these steps:

### 1. Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
```bash
python -m playwright install
```

### 3. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file to add your API keys
```

### 4. Create Directories
```bash
mkdir -p tmp/record_videos
mkdir -p tmp/traces  
mkdir -p tmp/agent_history
```

### 5. Run Application
```bash
python webui.py
```

## Configuration

### API Keys Setup

Edit the `.env` file to add your LLM provider API keys:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_api_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Ollama (local)
OLLAMA_ENDPOINT=http://localhost:11434
```

### Browser Settings

```env
# Use your own browser (optional)
CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"  # Windows
# CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # macOS

# User data directory (optional)
CHROME_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"  # Windows
# CHROME_USER_DATA="~/Library/Application Support/Google/Chrome/Profile 1"  # macOS

# Keep browser open between tasks
CHROME_PERSISTENT_SESSION=true
```

## Troubleshooting

### Common Issues

#### "Python not found"
- **Windows:** Reinstall Python and check "Add Python to PATH"
- **Linux/macOS:** Install Python 3.11+ using your package manager

#### "pip not found"
```bash
# Ubuntu/Debian
sudo apt install python3-pip

# macOS
python3 -m ensurepip --upgrade
```

#### "Playwright installation failed"
```bash
# Try manual installation
python -m playwright install chromium
python -m playwright install firefox
python -m playwright install webkit
```

#### "Permission denied" (Linux/macOS)
```bash
# Make scripts executable
chmod +x install.sh
chmod +x start_autonobot.sh
```

#### "Module not found" errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Port Already in Use
If port 7788 is already in use:
```bash
python webui.py --port 8080
```

### Browser Issues
- **Headless mode:** Add `headless=true` in browser settings
- **Security issues:** Enable "Disable Security" in browser settings
- **Custom browser:** Set `CHROME_PATH` in `.env` file

## Advanced Configuration

### Command Line Options
```bash
python webui.py --help

Options:
  --ip IP_ADDRESS     IP address to bind to (default: 127.0.0.1)
  --port PORT         Port to listen on (default: 7788)
  --theme THEME       UI theme (Ocean, Citrus, Glass, etc.)
  --dark-mode         Enable dark mode
  --auto-open         Automatically open browser
```

### Environment Variables
See `.env.example` for all available configuration options.

## Getting Help

- **Documentation:** [Browser Use Docs](https://docs.browser-use.com)
- **GitHub Issues:** [Report bugs](https://github.com/browser-use/web-ui/issues)
- **Discord:** [Join community](https://link.browser-use.com/discord)

## Next Steps

After installation:
1. **Configure API keys** in the `.env` file
2. **Open the web interface** at http://127.0.0.1:7788
3. **Test with a simple task** like "go to google.com and search for OpenAI"
4. **Explore the task queue features** for managing multiple automation tasks
