@echo off
echo =========================
echo UPDATE NILAI WEBSITE
echo =========================

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
echo Menambahkan perubahan ke GitHub...
git add .
git commit -m "Update nilai siswa otomatis"
git push origin main

IF %ERRORLEVEL% NEQ 0 (
    echo Terjadi kesalahan saat push ke GitHub!
    pause
    exit /b
)

echo.
echo SELESAI! Website akan update dalam beberapa detik.
pause