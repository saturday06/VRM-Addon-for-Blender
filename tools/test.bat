@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

setlocal
pushd "%~dp0.."
call uv run python -m unittest discover
echo on
popd
endlocal
pause
