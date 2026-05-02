@echo off
cd /d "%~dp0backend"
start "Kyosist" uvicorn main:app
timeout /t 2 /nobreak > nul
start http://localhost:8000
