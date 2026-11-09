@echo off

cd /d %~dp0\..\

rem python tools/fonts/gen_map.py --add 大宝节小宝节 -o tools/fonts/new
python.exe tools\fonts\gen_map.py -o tools\fonts\new

cd /d %~dp0
pause