@echo off
echo Starting HERFOO_TRADES Server...
echo.
cd /d "%~dp0"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
pause
