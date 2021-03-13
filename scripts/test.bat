setlocal
pushd "%~dp0.."
set PYTHONUTF8=1
call poetry run python -m unittest discover
echo on
popd
endlocal
pause
