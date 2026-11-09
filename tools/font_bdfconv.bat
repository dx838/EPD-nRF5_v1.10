@echo off

cd /d %~dp0

rem https://downloads.sourceforge.net/project/wqy/wqy-bitmapfont/1.0.0-RC1/wqy-bitmapsong-bdf-1.0.0-RC1.tar.gz

%~dp0font/bdfconv.exe -b 0 -f 1 -M %~dp0fonts/new/wqy9.map -n u8g2_font_wqy9_t_lunar  -o wqy9.c  %~dp0fonts/wenquanyi_9ptb.bdf
%~dp0font/bdfconv.exe -b 0 -f 1 -M %~dp0fonts/new/wqy12.map -n u8g2_font_wqy12_t_lunar -o wqy12.c %~dp0fonts/wenquanyi_12ptb.bdf

pause