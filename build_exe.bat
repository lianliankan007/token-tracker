@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE (
  where python >nul 2>nul
  if %errorlevel%==0 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
  echo Python not found. Please install Python 3.10+ first.
  pause
  exit /b 1
)

echo [1/3] Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo [2/3] Building EXE...
"%PYTHON_EXE%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name token-tracker ^
  --add-data "web;web" ^
  token_tracker.py

echo [3/3] Done.
echo EXE path: %~dp0dist\token-tracker.exe
pause
