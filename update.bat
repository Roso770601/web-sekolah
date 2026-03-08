@echo off
echo =========================
echo UPDATE WEBSITE SEKOLAH
echo =========================

REM =========================
REM AMBIL UPDATE TERBARU
REM =========================
echo Sinkronisasi dengan GitHub...
git pull origin main

REM =========================
REM KONVERSI EXCEL KE JSON
REM =========================
echo Mengubah Excel ke JSON...
python convert_excel_to_json.py

IF %ERRORLEVEL% NEQ 0 (
    echo Terjadi kesalahan saat konversi Excel ke JSON!
    pause
    exit /b
)

REM =========================
REM PUSH KE GITHUB
REM =========================
echo Mengirim update ke GitHub...

git add .
git commit -m "Update website sekolah"
git push origin main

IF %ERRORLEVEL% NEQ 0 (
    echo Terjadi kesalahan saat push ke GitHub!
    pause
    exit /b
)

echo.
echo SELESAI! Website akan update dalam beberapa detik.
pause