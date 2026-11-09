@echo off

cd /d %~dp0\..\

rem python tools/font/gen_map.py --add 大宝节小宝节 -o tools/font/new
python.exe tools\font\gen_map.py -o tools\font\new

cd /d %~dp0
pause