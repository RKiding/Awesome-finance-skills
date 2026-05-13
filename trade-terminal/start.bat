@echo off
echo Baslatiliyor...

:: Backend
start "Trade Terminal - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Frontend
timeout /t 2 /nobreak > nul
start "Trade Terminal - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Durdurmaniz icin acilan terminalleri kapatin.
