@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Virtual environment was not found.
    echo.
    echo Run this first:
    echo python -m venv .venv
    echo .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m app.main

if errorlevel 1 (
    echo.
    echo Application failed.
    pause
    exit /b 1
)
