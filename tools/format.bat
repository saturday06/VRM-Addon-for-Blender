setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
call poetry run ruff format %py_files%
call poetry run ruff check --fix %py_files%
echo on
popd
endlocal
endlocal
pause
