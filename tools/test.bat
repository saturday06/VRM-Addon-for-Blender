@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."

set no_pause=0
if "%1"=="/NoPause" set no_pause=1

call uv run python -m unittest discover
if %errorlevel% neq 0 goto :error

popd
goto :quit
:error
popd
exit /b 1
:quit
endlocal
if %no_pause% equ 0 pause
echo on
