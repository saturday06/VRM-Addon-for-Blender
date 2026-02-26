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
if %errorlevel% neq 0 goto :error

echo ### ruff check --fix ###
call uv run ruff check --fix
if %errorlevel% neq 0 goto :error

echo ### deno ###
where deno > nul
if %errorlevel% neq 0 (
  echo *** Please install `deno` command ***
  goto :error
)

echo ### shfmt ###
where shfmt > nul
if %errorlevel% neq 0 (
  echo *** Please install `shfmt` command ***
  goto :error
)
for /f "tokens=* usebackq" %%f in (`git ls-files "*.sh"`) do (
  call shfmt --write "%%f"
  if !errorlevel! neq 0 goto :error
)

echo ### deno fmt ###
call deno fmt
if %errorlevel% neq 0 goto :error

popd

goto :quit
:error
rem echo error
:quit
if %no_pause% equ 0 pause
endlocal
echo on
