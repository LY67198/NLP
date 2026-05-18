@echo off
chcp 65001 >nul
echo ============================================
echo   SmartChef - 智能厨房助手
echo ============================================
echo.

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

REM Check venv
if not exist "%VENV_PYTHON%" (
    echo [ERROR] venv not found: %VENV_PYTHON%
    pause
    exit /b 1
)

REM Check Ollama
echo [1/3] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not running, start with: ollama serve
) else (
    echo [OK] Ollama available
)

REM Start backend
echo [2/3] Starting backend on http://localhost:8000 ...
cd /d "%~dp0backend"
start "SmartChef-Backend" "%VENV_PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000
echo [OK] Backend window opened

REM Start frontend
echo [3/3] Starting frontend on http://localhost:3000 ...
cd /d "%~dp0frontend-vue"
start "SmartChef-Frontend" npx vite --port 3000
echo [OK] Frontend window opened

echo.
echo ============================================
echo   Opening http://localhost:3000 ...
echo ============================================
timeout /t 3 >nul
start http://localhost:3000
