@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later
@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
set UV_LINK_MODE=copy

echo ### uv sync ###
call uv sync
if %errorlevel% neq 0 goto :error

echo ### format (ruff format, ruff check --fix, shfmt, deno fmt) ###
call tools\format.bat /NoPause
if %errorlevel% neq 0 goto :error

echo ### lint (ruff, codespell, deno lint, pyright, vrm-validator) ###
call tools\lint.bat /NoPause
if %errorlevel% neq 0 goto :error

set skip_tests=0
if /I "%SKIP_TESTS%"=="1" set skip_tests=1
if /I "%SKIP_TESTS%"=="true" set skip_tests=1

if %skip_tests% equ 0 (
  echo ### tests (unittest discover) ###
  call tools\test.bat /NoPause
  if %errorlevel% neq 0 goto :error
) else (
  echo ### tests skipped (SKIP_TESTS=%SKIP_TESTS%) ###
)

popd
goto :quit
:error
popd
exit /b 1
:quit
endlocal
