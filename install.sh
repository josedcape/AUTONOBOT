#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "    AUTONOBOT Installation Script"
echo -e "========================================${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    if ! command_exists python; then
        echo -e "${RED}ERROR: Python is not installed${NC}"
        echo "Please install Python 3.11 or higher"
        echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo "macOS: brew install python3"
        echo "Or download from: https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION"

# Check Python version (basic check for 3.11+)
MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo -e "${RED}ERROR: Python version $PYTHON_VERSION is too old${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

echo -e "${GREEN}✓ Python version check passed${NC}"

# Check if pip is available
if ! command_exists pip3 && ! command_exists pip; then
    echo -e "${RED}ERROR: pip is not installed${NC}"
    echo "Please install pip:"
    echo "Ubuntu/Debian: sudo apt install python3-pip"
    echo "macOS: pip should be included with Python"
    exit 1
fi

# Determine pip command
if command_exists pip3; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# Create necessary directories
echo
echo "Creating directories..."
mkdir -p tmp/record_videos
mkdir -p tmp/traces
mkdir -p tmp/agent_history
echo -e "${GREEN}✓ Directories created${NC}"

# Install dependencies
echo
echo "Installing Python dependencies..."
echo "This may take a few minutes..."
$PIP_CMD install --upgrade pip
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to upgrade pip${NC}"
    exit 1
fi

$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    echo "Please check your internet connection and try again"
    exit 1
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Install Playwright browsers
echo
echo "Installing Playwright browsers..."
echo "This may take several minutes..."
$PYTHON_CMD -m playwright install
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Playwright browser installation failed${NC}"
    echo "You may need to install browsers manually later"
else
    echo -e "${GREEN}✓ Playwright browsers installed${NC}"
fi

# Setup environment file
echo
echo "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp ".env.example" ".env"
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create .env file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Environment file created from template${NC}"
else
    echo -e "${GREEN}✓ Environment file already exists${NC}"
fi

# Create launcher script
echo
echo "Creating launcher script..."
cat > start_autonobot.sh << 'EOF'
#!/bin/bash

echo "Starting AUTONOBOT Browser Use Web UI..."
echo
echo "Web UI will be available at: http://127.0.0.1:7788"
echo

# Determine Python command
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

$PYTHON_CMD webui.py --auto-open
EOF

chmod +x start_autonobot.sh
echo -e "${GREEN}✓ Launcher script created${NC}"

echo
echo -e "${BLUE}========================================"
echo -e "    Installation Complete!"
echo -e "========================================${NC}"
echo
echo "Next steps:"
echo "1. Edit .env file to add your API keys for LLM providers"
echo "2. Run ./start_autonobot.sh to launch the application"
echo "3. Or run: $PYTHON_CMD webui.py"
echo
echo "The web interface will be available at:"
echo "http://127.0.0.1:7788"
echo
echo "For help and documentation, visit:"
echo "https://github.com/browser-use/web-ui"
echo
