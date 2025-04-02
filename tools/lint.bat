@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1

for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )

echo ### ruff ###
call uv run ruff check
if %errorlevel% neq 0 goto :error

echo ### codespell ###
call uv run codespell %py_files%
if %errorlevel% neq 0 goto :error

echo ### mypy ###
call uv run mypy --show-error-codes .
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
call deno run pyright
if %errorlevel% neq 0 goto :error

echo ### vrm validator ###
call deno run vrm-validator
if %errorlevel% neq 0 goto :error

popd

goto :quit
:error
rem echo error
:quit
endlocal
endlocal
pause
echo on
