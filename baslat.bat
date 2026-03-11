@echo off
cd /d "%~dp0"
if not defined VIRTUAL_ENV (
    if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
)
python basla.py
pause
