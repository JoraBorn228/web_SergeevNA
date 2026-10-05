#!/usr/bin/env bash
# Run script for Git Bash / Linux / macOS
set -e

cd "$(dirname "$0")"

# --- Pick virtual environment (ve or venv) ---
PY="ve/Scripts/python.exe"
[ -f "$PY" ] || PY="venv/Scripts/python.exe"
# Linux/macOS layout
[ -f "$PY" ] || PY="ve/bin/python"
[ -f "$PY" ] || PY="venv/bin/python"

# --- Create environment if missing ---
if [ ! -f "$PY" ]; then
    echo "[run] Virtual environment not found, creating 've'..."
    python -m venv ve
    PY="ve/Scripts/python.exe"
    [ -f "$PY" ] || PY="ve/bin/python"
fi

# --- Install dependencies ---
echo "[run] Installing dependencies from ../requirements.txt ..."
"$PY" -m pip install -q -r ../requirements.txt

# --- Run the app ---
echo "[run] Starting Flask app: http://127.0.0.1:5000"
"$PY" app.py
