@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run.py --gui
) else (
    echo No se encontro la virtualenv en .venv\Scripts\python.exe
    exit /b 1
)
