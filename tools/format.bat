@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
set UV_LINK_MODE=copy

set no_pause=0
if "%1"=="/NoPause" set no_pause=1

echo ### ruff format ###
call uv run ruff format

echo ### ruff check --fix ###
call uv run ruff check --fix

echo ### Vite+ ###
where vp
if %errorlevel% neq 0 (
  echo *** Please install `vp` command ***
  goto :error
)
call vp install

echo ### Vite+ format ###
call vp fmt

popd

goto :quit
:error
rem echo error
:quit
if %no_pause% equ 0 pause
endlocal
echo on
