"""
AI AGENT WINDOWS SETUP - Simple & Fast
No fancy characters, just gets the job done
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def print_step(step, text):
    print(f"\n[Step {step}] {text}")

def print_ok(text):
    print(f"[OK] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_python():
    """Check Python installation"""
    success, output = run_command("python --version")
    if success:
        print_ok(f"Python: {output.strip()}")
        return True
    else:
        print_error("Python not found. Please install Python 3.8+")
        return False

def check_ollama():
    """Check if Ollama is installed"""
    print("\nChecking Ollama...")
    
    # Check if ollama command exists
    success, _ = run_command("ollama --version")
    
    if not success:
        print_error("Ollama not found!")
        print("\nPlease install Ollama:")
        print("1. Go to: https://ollama.ai")
        print("2. Download and install")
        print("3. Run this script again")
        return False
    
    print_ok("Ollama is installed")
    
    # Check if ollama is running
    success, _ = run_command("curl -s http://localhost:11434")
    
    if not success:
        print("\nOllama is not running. Starting it now...")
        print("Opening new window for Ollama...")
        
        # Start ollama in new window
        subprocess.Popen("start cmd /k ollama serve", shell=True)
        
        import time
        print("Waiting 5 seconds for Ollama to start...")
        time.sleep(5)
    else:
        print_ok("Ollama is running")
    
    return True

def create_directories():
    """Create necessary directories"""
    print_step(1, "Creating directories...")
    
    dirs = [
        "agent_memory",
        "agent_logs", 
        "agent_data",
        "agent_secure",
        "agent_cache"
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print_ok(f"Created: {dir_name}/")
    
    return True

def create_requirements():
    """Create requirements.txt"""
    print_step(2, "Creating requirements.txt...")
    
    content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
python-dotenv==1.0.0
langchain-ollama
langchain-core
chromadb
sentence-transformers
duckduckgo-search
requests
beautifulsoup4
lxml
aiohttp
pyautogui
pillow
psutil
cryptography
pydantic
diskcache
"""
    
    with open("requirements.txt", "w") as f:
        f.write(content)
    
    print_ok("Created requirements.txt")
    return True

def create_env_file():
    """Create .env configuration"""
    print_step(3, "Creating .env configuration...")
    
    content = """# AI Agent Configuration
AGENT_MODEL=llama3.1:8b
AGENT_TEMP=0.7
AGENT_MAX_ITER=15

# API Keys (optional - leave empty if not using)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Security
SECRET_KEY=change-this-in-production
"""
    
    with open(".env", "w") as f:
        f.write(content)
    
    print_ok("Created .env")
    return True

def create_start_script():
    """Create Windows start script"""
    print_step(4, "Creating start.bat...")
    
    content = """@echo off
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
"""
    
    with open("start.bat", "w") as f:
        f.write(content)
    
    print_ok("Created start.bat")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step(5, "Installing Python packages...")
    print("This may take a few minutes...")
    
    success, output = run_command("pip install -r requirements.txt")
    
    if success:
        print_ok("All packages installed!")
        return True
    else:
        print_error("Some packages failed to install")
        print(output)
        return False

def pull_ollama_model():
    """Pull the Ollama model"""
    print_step(6, "Pulling Ollama model...")
    print("This will download llama3.1:8b (about 4.7GB)")
    print("This may take 5-15 minutes depending on your connection...")
    
    success, output = run_command("ollama pull llama3.1:8b")
    
    if success:
        print_ok("Model downloaded successfully!")
        return True
    else:
        print_error("Failed to pull model")
        print(output)
        return False

def create_readme():
    """Create README"""
    content = """# AI Agent - Quick Start

## Running Your Agent

1. Make sure Ollama is running:
   - Open Command Prompt
   - Run: ollama serve
   - Keep this window open

2. Start the agent:
   - Double-click: start.bat
   - Or run: python api_server.py

3. Open browser:
   - Go to: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Your Files

- agent_code.py - Your main agent (rename your original script)
- api_server.py - Web API server
- .env - Configuration settings
- start.bat - Easy start script

## Configuration

Edit .env to change:
- Model (llama3.1:8b, gpt-4, etc.)
- Temperature (0.0-1.0)
- API keys for cloud models

## Troubleshooting

Problem: "Ollama not running"
Solution: Open new terminal and run: ollama serve

Problem: "Port 8000 already in use"
Solution: Close other applications using port 8000

Problem: "Module not found"
Solution: Run: pip install -r requirements.txt

## Next Steps

1. Rename your original agent script to: agent_code.py
2. Save the FastAPI backend as: api_server.py
3. Run: start.bat

Enjoy your AI agent!
"""
    
    with open("README.md", "w") as f:
        f.write(content)
    
    print_ok("Created README.md")

def main():
    """Main setup function"""
    print_header("AI AGENT SETUP FOR WINDOWS")
    print("This will set up everything you need\n")
    
    # Check Python
    if not check_python():
        input("\nPress Enter to exit...")
        return
    
    # Create structure
    create_directories()
    create_requirements()
    create_env_file()
    create_start_script()
    create_readme()
    
    # Ask about installation
    print("\n" + "="*60)
    print("Setup files created!")
    print("="*60)
    
    print("\nDo you want to:")
    print("1. Install Python packages now (recommended)")
    print("2. Skip for now (install manually later)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        install_dependencies()
    else:
        print("\nSkipping package installation")
        print("Install later with: pip install -r requirements.txt")
    
    # Check Ollama
    print("\n" + "="*60)
    ollama_ok = check_ollama()
    
    if ollama_ok:
        print("\nDo you want to download the AI model now?")
        print("This will download llama3.1:8b (4.7GB)")
        choice = input("Download now? (y/n): ").strip().lower()
        
        if choice == 'y':
            pull_ollama_model()
        else:
            print("\nSkipping model download")
            print("Download later with: ollama pull llama3.1:8b")
    
    # Final message
    print("\n" + "="*60)
    print_header("SETUP COMPLETE!")
    
    print("\nNext Steps:")
    print("-" * 60)
    print("1. Save your original agent script as: agent_code.py")
    print("2. Save the FastAPI backend as: api_server.py")
    print("3. Run: start.bat")
    print("4. Open browser: http://localhost:8000")
    print("-" * 60)
    
    print("\nQuick Start Command:")
    print("  start.bat")
    
    print("\nManual Start:")
    print("  Terminal 1: ollama serve")
    print("  Terminal 2: python api_server.py")
    
    print("\nDocumentation: README.md")
    print("\n" + "="*60)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
    except Exception as e:
        print(f"\n\nSetup failed: {e}")
        input("Press Enter to exit...")