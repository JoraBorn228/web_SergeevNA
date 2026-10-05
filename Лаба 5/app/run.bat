@echo off
setlocal
cd /d "%~dp0"

rem --- Pick virtual environment (ve or venv) ---
set "PY=ve\Scripts\python.exe"
if not exist "%PY%" set "PY=venv\Scripts\python.exe"

rem --- Create environment if missing ---
if not exist "%PY%" (
    echo [run] Virtual environment not found, creating "ve"...
    python -m venv ve
    set "PY=ve\Scripts\python.exe"
)

rem --- Install dependencies ---
echo [run] Installing dependencies from ..\requirements.txt ...
"%PY%" -m pip install -q -r "..\requirements.txt"

rem --- Run the app ---
echo [run] Starting Flask app: http://127.0.0.1:5000
"%PY%" app.py
