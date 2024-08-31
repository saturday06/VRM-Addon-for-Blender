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
echo ### pyright ###
call uv run pyright %py_files% %pyi_files%
echo ### prettier ###
where npm
if %errorlevel% equ 0 call npm exec --yes -- prettier --write .
popd
endlocal
endlocal
pause
