setlocal
pushd "%~dp0.."
call poetry run python -m unittest discover
echo on
popd
endlocal
pause
