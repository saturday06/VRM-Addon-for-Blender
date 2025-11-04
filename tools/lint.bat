@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
set UV_LINK_MODE=copy

set no_pause=0
if "%1"=="/NoPause" set no_pause=1

for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )

echo ### ruff ###
call uv run ruff check
if %errorlevel% neq 0 goto :error

echo ### codespell ###
call uv run codespell %py_files%
if %errorlevel% neq 0 goto :error

echo ### deno ###
where deno > nul
if %errorlevel% neq 0 (
  echo *** Please install `deno` command ***
  goto :error
)

echo ### deno lint ###
call deno lint
if %errorlevel% neq 0 goto :error

echo ### pyright ###
call deno task pyright
if %errorlevel% neq 0 goto :error

echo ### vrm validator ###
call deno task vrm-validator
if %errorlevel% neq 0 goto :error

popd

goto :quit
:error
rem echo error
:quit
if %no_pause% equ 0 pause
endlocal
echo on
