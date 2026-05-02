@echo off
cd /d "%~dp0"
start "Kyosist" uvicorn run:app
timeout /t 2 /nobreak > nul
start http://localhost:8000
