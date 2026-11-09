@echo off

cd /d %~dp0/../

python.exe tools/fonts/check_font.py %~1

cd /d %~dp0/
pause