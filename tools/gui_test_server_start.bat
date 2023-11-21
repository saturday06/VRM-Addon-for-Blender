cd /d "%~dp0.."
md var\log
md var\tmp

echo "%cd%" > var\tmp\repository_root_path.txt

set powershell_command=powershell
where pwsh
if %errorlevel% equ 0 set powershell_command=pwsh
%powershell_command% -Command "Write-Output (Get-FileHash 'var/tmp/repository_root_path.txt').Hash.ToLower()" > var\repository_root_path_hash.txt
for /f "usebackq delims=" %%A in (`type var\repository_root_path_hash.txt`) do set hash=%%A

set container_name=vrm_addon_for_blender_gui_test_container_%hash%
set tag_name=vrm_addon_for_blender_gui_test_%hash%

for /f "usebackq delims=" %%A in (`docker ps --quiet --filter "name=%container_name%"`) do set running_container=%%A

if "%running_container%" neq "" goto test_web_connection

call docker build ^
  . ^
  --file tools\gui_test_server.dockerfile ^
  --tag %tag_name%
if %errorlevel% neq 0 goto error

call docker run ^
  --detach ^
  --publish 127.0.0.1:6080:6080/tcp ^
  --volume "%cd%\var":/root/var ^
  --volume "%cd%\tests\resources\gui":/root/tests ^
  --volume "%cd%\src\io_scene_vrm":/root/io_scene_vrm ^
  --rm ^
  --name %container_name% ^
  %tag_name%
if %errorlevel% neq 0 goto error

:test_web_connection
%powershell_command% -Command "foreach ($retry in 1..30) { try { Invoke-WebRequest -Uri http://127.0.0.1:6080/vnc.html; if ($?) { Exit 0 }  } catch { }; sleep 1 }; Exit 1"
if %errorlevel% neq 0 goto error

exit /b 0

:error
exit /b 1
