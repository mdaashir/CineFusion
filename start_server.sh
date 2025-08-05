#!/bin/bash
# CineFusion Development Setup and Server Launcher
# Unix/Linux/macOS Shell Script

echo ""
echo "========================================"
echo "   CineFusion Development Server"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Error: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ from https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Display Python version
echo "Checking Python installation..."
$PYTHON_CMD --version

# Check if we're in the right directory
if [[ ! -f "package.json" ]] && [[ ! -d "Frontend" ]]; then
    echo "❌ Error: This script must be run from the CineFusion project root directory"
    echo "Make sure you have Frontend folder and package.json in the current directory"
    exit 1
fi

echo ""
echo "🚀 Starting CineFusion development server..."
echo ""
echo "💡 Tips:"
echo "   • Press Ctrl+C to stop the server"
echo "   • The browser will open automatically"
echo "   • Server will run on http://localhost:8000"
echo ""

# Make the script executable if it isn't already
chmod +x dev_server.py 2>/dev/null

# Start the development server
$PYTHON_CMD dev_server.py

echo ""
echo "✅ Server has stopped."
