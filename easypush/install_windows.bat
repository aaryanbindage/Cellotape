@echo off
setlocal enabledelayedexpansion
title EasyPush Installer

echo.
echo  ============================================
echo    EasyPush Installer -- Windows
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Download from: https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo  [OK] %PY_VER%

:: Check Git
git --version >nul 2>&1
if errorlevel 1 (
    echo  [WARN] Git not found. Download from: https://git-scm.com
    echo  EasyPush will not work until Git is installed.
) else (
    for /f "tokens=*" %%i in ('git --version') do set GIT_VER=%%i
    echo  [OK] %GIT_VER%
)

echo.
echo  Installing Python dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install customtkinter --quiet
echo  [OK] customtkinter installed

:: Get the directory of this script
set SCRIPT_DIR=%~dp0

:: Create launcher scripts in the EasyPush folder
echo.
echo  Creating launchers...

:: GUI launcher
echo @echo off > "%SCRIPT_DIR%launch_gui.bat"
echo start "" python "%SCRIPT_DIR%easypush.py" >> "%SCRIPT_DIR%launch_gui.bat"
echo  [OK] launch_gui.bat created

:: CLI wrapper
echo @echo off > "%SCRIPT_DIR%easypush.bat"
echo python "%SCRIPT_DIR%easypush_cli.py" %%* >> "%SCRIPT_DIR%easypush.bat"
echo  [OK] easypush.bat created

:: Add to user PATH
set "USER_PATH="
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"

echo !USER_PATH! | find /i "%SCRIPT_DIR%" >nul 2>&1
if errorlevel 1 (
    if "!USER_PATH!"=="" (
        setx PATH "%SCRIPT_DIR%" >nul
    ) else (
        setx PATH "!USER_PATH!;%SCRIPT_DIR%" >nul
    )
    echo  [OK] Added EasyPush to your PATH
) else (
    echo  [OK] Already in PATH
)

:: Create desktop shortcut for GUI
set SHORTCUT_PATH=%USERPROFILE%\Desktop\EasyPush.bat
echo @echo off > "%SHORTCUT_PATH%"
echo start "" python "%SCRIPT_DIR%easypush.py" >> "%SHORTCUT_PATH%"
echo  [OK] Desktop shortcut created: EasyPush.bat

echo.
echo  ============================================
echo   Installation complete!
echo  ============================================
echo.
echo  Launch GUI:   Double-click EasyPush.bat on your Desktop
echo               OR run: launch_gui.bat
echo.
echo  CLI usage:   Open a NEW terminal window, then type:
echo               easypush config   (set up first)
echo               easypush push     (push files)
echo               easypush gui      (open GUI)
echo.
echo  NOTE: Open a new terminal window for PATH changes to take effect.
echo.
pause
