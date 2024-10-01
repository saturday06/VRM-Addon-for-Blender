@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1

echo ### ruff format ###
call uv run ruff format

echo ### ruff check --fix ###
call uv run ruff check --fix

echo ### npm ###
where npm
if %errorlevel% neq 0 (
  echo *** Please install `npm` command ***
  goto :error
)

echo ### prettier ###
call npm exec --yes -- prettier --write .

popd

goto :quit
:error
rem echo error
:quit
endlocal
endlocal
pause
echo on
