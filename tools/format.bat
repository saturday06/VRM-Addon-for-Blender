@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1

echo ### ruff format ###
call uv run ruff format

echo ### ruff check --fix ###
call uv run ruff check --fix

where npm > nul
if %errorlevel% equ 0 (
  echo ### prettier ###
  call npm exec --yes -- prettier --write .
)

popd
endlocal
endlocal
pause
echo on
