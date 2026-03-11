@echo off
cd /d "%~dp0"
set /p SURUM="Surum numarasi girin (ornek: v21.1): "
if "%SURUM%"=="" set SURUM=v21_guncelleme
set PAKET=ERP_%SURUM%_guncelleme
echo Paket olusturuluyor: %PAKET%
if exist "%PAKET%" rmdir /s /q "%PAKET%"
mkdir "%PAKET%"
xcopy /E /I /Q app "%PAKET%\app" >nul
copy basla.py "%PAKET%\" >nul
copy config.py "%PAKET%\" >nul
copy moduller.json "%PAKET%\" >nul
copy requirements.txt "%PAKET%\" >nul
copy veritabani_guncelle.py "%PAKET%\" >nul
copy setup_wizard.py "%PAKET%\" >nul
copy kurulum.bat "%PAKET%\" >nul
copy baslat.bat "%PAKET%\" >nul
copy run.py "%PAKET%\" >nul
echo Guncelleme talimatlari: > "%PAKET%\GUNCELLEME.txt"
echo 1. Bu klasordeki dosyalari ERP kurulum dizinine kopyalayin. >> "%PAKET%\GUNCELLEME.txt"
echo 2. python veritabani_guncelle.py calistirin. >> "%PAKET%\GUNCELLEME.txt"
echo 3. baslat.bat ile sistemi calistirin. >> "%PAKET%\GUNCELLEME.txt"
powershell -Command "Compress-Archive -Path '%PAKET%\*' -DestinationPath '%PAKET%.zip' -Force"
if exist "%PAKET%.zip" rmdir /s /q "%PAKET%"
echo.
echo Tamamlandi: %PAKET%.zip
pause
