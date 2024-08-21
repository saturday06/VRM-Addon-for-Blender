setlocal
pushd "%~dp0.."
call uv run python -m unittest discover
echo on
popd
endlocal
pause
