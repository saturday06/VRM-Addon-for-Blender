---
title: 'Development How-To'
prev:
  text: 'Automation with Python scripts'
  link: '../scripting-api.html'
next: false
---

[The repository](https://github.com/saturday06/VRM-Addon-for-Blender) contains
source code, code formatting settings, code type checking settings, and software
testing settings. These are strongly dependent on the tool
[astral-sh/uv](https://docs.astral.sh/uv/), so you will need to install that
first. Alternatively, you can use [Dev Container](https://containers.dev/) to
set them up automatically.

## Link the repository to the add-on folder

The
[src/io_scene_vrm](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm)
folder in the GitHub repository contains the main add-on code. For efficient
development, you can create a link to this folder in Blender's `user_default` or
`addons` directory.

```text
# Blender 4.2 or later

# Linux
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/extensions/user_default/vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/extensions/user_default/vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" src\io_scene_vrm

# Blender 4.1.1 or earlier

# Linux
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" src\io_scene_vrm
```

## To format the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\format.bat` in the repository to run it.

## To format the code in Visual Studio Code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. In the Visual Studio Code terminal, run the `uv sync` command.
3. Run Visual Studio Code's `Format Document`.

The same result can be achieved by using the `Ruff` extension in Visual Studio
Code.

## To run type checking of the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\lint.bat` in the repository and run it.

## To run type checking of the code in Visual Studio Code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. In the Visual Studio Code terminal, run the `uv sync` command.
3. Install the `Ruff` and `Pyright` extensions in Visual Studio Code.
4. Open the Python file you want to type check.

## To run the software tests of the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\test.bat` in the repository and run it.
3. If you get the error `Blender not found`, set the environment variable
   `BLENDER_VRM_TEST_BLENDER_PATH` to the path of the Blender LTS exe file.

## To run the software tests of the code in Visual Studio Code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. In the Visual Studio Code terminal, run the `uv sync` command.
3. Select `Testing` from the left icon in Visual Studio Code.
4. Select `Configure Python Tests`.
5. Select `unittests` as the test library.
6. Select `Root Directory` as the test folder.
7. Select `test_*` as the test file pattern.
8. Press `Run Tests`.
9. If you get the error `Blender not found`, set the environment variable
   `BLENDER_VRM_TEST_BLENDER_PATH` to the path of the Blender LTS exe file.
