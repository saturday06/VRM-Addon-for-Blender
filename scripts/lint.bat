@echo off
setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
echo ### poetry check ###
poetry check
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
echo ### codespell ###
call poetry run codespell %py_files%
echo ### mypy ###
call poetry run mypy --show-error-codes %py_files%
echo ### flake8 ###
call poetry run flake8 --count --show-source --statistics %py_files%
echo ### pylint ###
call poetry run pylint %py_files%
echo ### pyright ###
call poetry run pyright %py_files%
popd
endlocal
endlocal
pause
