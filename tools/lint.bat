@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
echo ### poetry check ###
poetry check
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
for /f "tokens=* usebackq" %%f in (`git ls-files "*.pyi"`) do ( set pyi_files=!pyi_files! %%f )
echo ### ruff ###
call poetry run ruff check %py_files% %pyi_files%
echo ### codespell ###
call poetry run codespell %py_files%
echo ### mypy ###
call poetry run mypy --show-error-codes %py_files% %pyi_files%
echo ### pyright ###
call poetry run pyright %py_files% %pyi_files%
popd
endlocal
endlocal
pause
