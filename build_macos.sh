#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_EXE="${PYTHON_EXE:-python3}"
APP_NAME="token-tracker"
DMG_NAME="${APP_NAME}.dmg"

echo "[1/3] Installing dependencies..."
"$PYTHON_EXE" -m pip install --upgrade pip
"$PYTHON_EXE" -m pip install -r requirements.txt

echo "[2/3] Building macOS .app..."
"$PYTHON_EXE" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --add-data "web:web" \
  token_tracker.py

echo "[3/3] Creating DMG..."
if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found. This script must run on macOS."
  exit 1
fi

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
  echo "App bundle not found: $APP_PATH"
  exit 1
fi

rm -f "dist/${DMG_NAME}"
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$APP_PATH" \
  -ov \
  -format UDZO \
  "dist/${DMG_NAME}"

echo "Done."
echo "App: $(pwd)/dist/${APP_NAME}.app"
echo "DMG: $(pwd)/dist/${DMG_NAME}"
