@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1

echo ### ruff format ###
call uv run ruff format

echo ### ruff check --fix ###
call uv run ruff check --fix

echo ### deno ###
where deno
if %errorlevel% neq 0 (
  echo *** Please install `deno` command ***
  goto :error
)

echo ### deno fmt ###
call deno fmt

popd

goto :quit
:error
rem echo error
:quit
endlocal
endlocal
pause
echo on
