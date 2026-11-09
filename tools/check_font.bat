@echo off

cd /d %~dp0/../

python.exe tools/font/check_font.py %~1

cd /d %~dp0/
pause