#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_EXE="${PYTHON_EXE:-python3}"

echo "[1/3] Installing dependencies..."
"$PYTHON_EXE" -m pip install --upgrade pip
"$PYTHON_EXE" -m pip install -r requirements.txt

echo "[2/3] Building macOS app..."
"$PYTHON_EXE" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onefile \
  --name token-tracker \
  --add-data "web:web" \
  token_tracker.py

echo "[3/3] Done."
echo "Binary: $(pwd)/dist/token-tracker"
