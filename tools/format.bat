setlocal
setlocal enabledelayedexpansion
pushd "%~dp0.."
set PYTHONUTF8=1
for /f "tokens=* usebackq" %%f in (`git ls-files "*.py"`) do ( set py_files=!py_files! %%f )
for /f "tokens=* usebackq" %%f in (`git ls-files "*.pyi"`) do ( set pyi_files=!pyi_files! %%f )
call poetry run ruff format %py_files% %pyi_files%
call poetry run ruff check --fix %py_files% %pyi_files%
echo on
popd
endlocal
endlocal
pause
