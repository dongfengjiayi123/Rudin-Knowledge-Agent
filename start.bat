@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env >nul
.venv\Scripts\python.exe -m rudin_agent.cli serve
pause
