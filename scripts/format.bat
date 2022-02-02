setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
call poetry run autoflake --in-place --remove-all-unused-imports --remove-unused-variables %py_files%
echo on
call poetry run isort %py_files%
echo on
call poetry run black %py_files%
echo on
popd
endlocal
endlocal
pause
