cd /d "%~dp0.."
md logs
md tmp

cd > tmp\repository_root_path.txt

set powershell_command=powershell
where pwsh
if %errorlevel% equ 0 set powershell_command=pwsh
%powershell_command% -Command "Write-Output (Get-FileHash 'tmp/repository_root_path.txt').Hash.ToLower()" > tmp\repository_root_path_hash.txt
for /f "usebackq delims=" %%A in (`type tmp\repository_root_path_hash.txt`) do set hash=%%A

set container_name=vrm_addon_for_blender_gui_test_container_%hash%
set tag_name=vrm_addon_for_blender_gui_test_%hash%

for /f "usebackq delims=" %%A in (`docker ps --quiet --filter "name=%container_name%"`) do set running_container=%%A

if "%running_container%" neq "" goto ok

call docker build ^
  . ^
  --file scripts\gui_test_server.dockerfile ^
  --tag %tag_name%

call docker run ^
  --detach ^
  --publish 127.0.0.1:6080:6080/tcp ^
  --volume "%cd%\logs":/root/logs ^
  --volume "%cd%\tests\resources\gui":/root/tests ^
  --volume "%cd%\io_scene_vrm":/root/io_scene_vrm ^
  --rm ^
  --name %container_name% ^
  %tag_name%

:ok
