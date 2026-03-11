@echo off
cd /d "%~dp0"
echo ERP v21 - Kutuphaneleri Kur
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo https://www.python.org/downloads adresinden indirin.
    pause
    exit /b 1
)
echo Python bulundu.
echo.
echo Kutuphaneler kuruluyor...
pip install -r requirements.txt
echo.
echo Veritabani hazirlaniyor...
python veritabani_guncelle.py
echo.
echo Kurulum tamamlandi! Sistemi baslatmak icin baslat.bat calistirin.
pause
