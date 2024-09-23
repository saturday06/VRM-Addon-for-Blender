@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
for /f "tokens=* usebackq" %%f in (`git ls-files "*.pyi"`) do ( set pyi_files=!pyi_files! %%f )

echo ### ruff ###
call uv run ruff check %py_files% %pyi_files%
echo ### codespell ###
call uv run codespell %py_files%
echo ### mypy ###
call uv run mypy --show-error-codes %py_files% %pyi_files%

where npm
if %errorlevel% equ 0 call npm install

echo ### pyright ###
where npm
if %errorlevel% equ 0 call npm exec --yes -- pyright --warnings --pythonpath .venv\bin\python3.exe
echo ### prettier ###
where npm
if %errorlevel% equ 0 call npm exec --yes -- prettier --write .
echo ### vrm validator ###
where npm
if %errorlevel% equ 0 call npm exec --yes --package=gltf-validator -- node .\tools\vrm_validator.js

popd
endlocal
endlocal
pause
