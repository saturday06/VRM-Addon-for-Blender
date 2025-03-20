@rem SPDX-License-Identifier: MIT OR GPL-3.0-or-later

@echo off
setlocal

cd /d "%~dp0.."

for /f %%i in (
  'powershell -Command "[System.BitConverter]::ToString((New-Object System.Security.Cryptography.SHA256Managed).ComputeHash([System.Text.Encoding]::UTF8.GetBytes($PWD))).ToLower().Replace(\"-\", \"\")"'
) do set pwd_hash=%%i
set super_linter_tag_name="super-linter-local-windows-%pwd_hash%"

docker build --platform=linux/amd64 --tag "%super_linter_tag_name%" --file tools/super-linter.dockerfile .
docker run -v "%cd%:/tmp/lint" "%super_linter_tag_name%"

endlocal
exit /b
