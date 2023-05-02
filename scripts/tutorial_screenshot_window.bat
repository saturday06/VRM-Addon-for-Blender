@echo off
echo ============== Launching tutorial window ===============
echo Please check following conditions:
echo - Launched blender version is a latest lts.
echo - Current screen zoom settings is 200%%.
echo - Set the desktop background color to black.
echo - Simplify the file view as much as possible.
echo - In English, set the interface font to an empty string.
echo - In Japanese, set the interface font to Meiryo.
rem Blender uses customized NotoSansCJK but it cannot display Japanese Kanji correctly.
rem We need to use NotoSansCJKjp instead. But it's not installed on the system.
rem And currently Yu Gothic is not available.
echo ========================================================
pause
@echo on
blender-launcher.exe --window-geometry 0 0 1320 1320
pause
