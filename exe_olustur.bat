@echo off
cd /d "%~dp0"
echo.
echo ERP v21 - EXE Olusturucu
echo ========================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo python.org adresinden Python 3.8 veya uzeri indirin.
    pause
    exit /b 1
)

echo [1/3] PyInstaller kuruluyor...
pip install pyinstaller >nul 2>&1
echo Tamam

echo [2/3] EXE olusturuluyor (2-5 dakika bekleyin)...
pyinstaller --onefile --noconsole --name ERP_v21_Kurulum --add-data "app;app" --add-data "moduller.json;." --add-data "requirements.txt;." --add-data "veritabani_guncelle.py;." --add-data "basla.py;." --add-data "config.py;." --hidden-import flask --hidden-import flask_sqlalchemy --hidden-import sqlalchemy --hidden-import openpyxl --hidden-import jinja2 --hidden-import werkzeug --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.messagebox --hidden-import tkinter.filedialog setup_wizard.py

if errorlevel 1 (
    echo HATA: EXE olusturulamadi. build_log.txt dosyasina bakin.
    pause
    exit /b 1
)

echo [3/3] Temizlik yapiliyor...
if exist build rmdir /s /q build
if exist ERP_v21_Kurulum.spec del /q ERP_v21_Kurulum.spec

echo.
echo ===========================================
echo TAMAMLANDI!
echo dist\ERP_v21_Kurulum.exe hazir
echo ===========================================
echo.
explorer dist
pause
