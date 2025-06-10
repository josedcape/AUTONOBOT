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
