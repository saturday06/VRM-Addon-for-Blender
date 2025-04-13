@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal

cd /d "%~dp0.."

docker build --tag super-linter-local --file tools/super-linter.dockerfile .
docker run -e "RUN_LOCAL=true" -v "%cd%:/tmp/lint" super-linter-local

endlocal
exit /b
