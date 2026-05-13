@echo off
echo ===================================
echo  Trade Terminal - Windows Kurulum
echo ===================================
echo.

:: Backend
echo [1/4] Backend Python ortami kuruluyor...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
    copy .env.example .env
    echo  .env dosyasi olusturuldu. API key leri ekleyin: backend\.env
)
cd ..

:: Frontend
echo.
echo [2/4] Frontend bagımliliklari yukleniyor...
cd frontend
call npm install
if not exist .env.local (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo NEXT_PUBLIC_WS_URL=ws://localhost:8000 >> .env.local
    echo  .env.local olusturuldu.
)
cd ..

echo.
echo [3/4] Bot klasoru olusturuluyor...
if not exist backend\bots mkdir backend\bots
if not exist backend\logs\bots mkdir backend\logs\bots
if not exist backend\configs\bots mkdir backend\configs\bots
if not exist backend\data mkdir backend\data

echo.
echo ===================================
echo  Kurulum tamamlandi!
echo.
echo  Sonraki adimlar:
echo  1. backend\.env dosyasina API key lerini ekle
echo  2. start.bat ile baslatabilirsin
echo ===================================
pause
