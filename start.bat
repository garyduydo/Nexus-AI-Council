@echo off
echo ============================================
echo Starting AI Agent...
echo ============================================
echo.

echo [1/3] Checking Ollama...
curl -s http://localhost:11434 >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama not running!
    echo Please start Ollama first:
    echo   1. Open new terminal
    echo   2. Run: ollama serve
    echo.
    pause
    exit
)
echo OK: Ollama is running

echo.
echo [2/3] Starting API Server...
echo.
python api_server.py

pause
