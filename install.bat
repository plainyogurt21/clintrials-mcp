@echo off
REM Installation script for Clinical Trials MCP Server (Windows)

echo 🏥 Installing Clinical Trials MCP Server...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Using Python: 
python --version

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies.
    pause
    exit /b 1
)

REM Test the installation
echo 🧪 Testing installation...
python test_server.py
if %errorlevel% neq 0 (
    echo ❌ Installation test failed. Please check the logs above.
    pause
    exit /b 1
)

echo ✅ Installation successful!
echo.
echo 🚀 Usage:
echo   Direct: python mcp_server.py
echo   Via setup: python setup.py install
echo.
echo 📖 Configuration for Claude Desktop:
echo   Add to claude_desktop_config.json:
echo   {
echo     "mcpServers": {
echo       "clinicaltrials": {
echo         "command": "python",
echo         "args": ["%CD%\mcp_server.py"],
echo         "env": {}
echo       }
echo     }
echo   }

pause