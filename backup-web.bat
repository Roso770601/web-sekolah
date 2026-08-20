@echo off
echo ======================================
echo        BACKUP WEBSITE SDN 1 SUKAMANAH
echo ======================================

set "SOURCE=C:\web"
set "DEST=D:\Backup-Web-Sekolah"
set "ZIPFILE=%DEST%\backup-web-sekolah.zip"

if not exist "%DEST%" mkdir "%DEST%"

echo.
echo Menghapus backup lama...
if exist "%ZIPFILE%" del "%ZIPFILE%"

echo.
echo Sedang membuat backup...
powershell -NoProfile -Command "Compress-Archive -Path '%SOURCE%\*' -DestinationPath '%ZIPFILE%' -Force"

echo.
echo ======================================
echo BACKUP SELESAI!
echo File:
echo %ZIPFILE%
echo ======================================

pause