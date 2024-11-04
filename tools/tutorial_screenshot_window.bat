@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
echo ============== Launching tutorial window ===============
echo Please check following conditions:
echo - Launched blender version is a latest lts.
echo - Current screen zoom settings is 200%%.
echo - Set the desktop background color to black.
echo - Simplify the file view as much as possible.
echo - Make sure generated screenshot size is 1320x1080.
echo - In English, set the interface font to an empty string.
echo - In Japanese, set the interface font to "Meiryo Regular" (meiryo.ttc).
rem Blender uses customized NotoSansCJK but it cannot display Japanese Kanji correctly.
rem We need to use NotoSansCJKjp instead. But it's not installed on the system.
rem And I think "Yu Gothic" looks thin and not suitable for screenshots.
echo ========================================================
pause
@echo on
blender-launcher.exe --window-geometry 0 0 1316 1020
pause
