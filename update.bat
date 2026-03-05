@echo off

echo =========================
echo UPDATE NILAI WEBSITE
echo =========================

echo Mengubah Excel ke JSON...
python convert_excel_to_json.py

echo.
echo Mengirim ke GitHub...

git add .
git commit -m "update nilai siswa"
git push origin main

echo.
echo SELESAI! Website akan update dalam beberapa detik.
pause