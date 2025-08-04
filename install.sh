#!/bin/bash
# Installation script for Clinical Trials MCP Server

set -e

echo "🏥 Installing Clinical Trials MCP Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Using Python: $($PYTHON_CMD --version)"

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.8+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Install pip if not available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# Install dependencies
echo "📦 Installing dependencies..."
$PIP_CMD install -r requirements.txt

# Make the binary executable
chmod +x bin/clintrials-mcp

# Test the installation
echo "🧪 Testing installation..."
if $PYTHON_CMD test_server.py; then
    echo "✅ Installation successful!"
    echo ""
    echo "🚀 Usage:"
    echo "  Direct: python mcp_server.py"
    echo "  Via bin: ./bin/clintrials-mcp"
    echo ""
    echo "📖 Configuration for Claude Desktop:"
    echo '  Add to claude_desktop_config.json:'
    echo '  {'
    echo '    "mcpServers": {'
    echo '      "clinicaltrials": {'
    echo '        "command": "python",'
    echo '        "args": ["'$(pwd)'/mcp_server.py"],'
    echo '        "env": {}'
    echo '      }'
    echo '    }'
    echo '  }'
else
    echo "❌ Installation test failed. Please check the logs above."
    exit 1
fi