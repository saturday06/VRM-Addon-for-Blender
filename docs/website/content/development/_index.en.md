---
title: "Development How-To"
---

The repository contains code formatting settings, code type checking settings, and software testing settings.

These are strongly dependent on the tool [astral-sh/uv](https://docs.astral.sh/uv/), so you will need to install that first.
Alternatively, you can use Visual Studio Code's devcontainer to set them up automatically.

## Link the repository to the add-on folder

The source code for development is in the [main](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main) branch. Its [src/io_scene_vrm](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm) folder is a main body of the add-on. For efficient development, you can create a link to that folder in the Blender `addons` folder.

```text
# Repository setup
git checkout main

# Blender 4.2 or later

# Linux
ln -s "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/extensions/user_default/vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/extensions/user_default/vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" src\io_scene_vrm

# Blender 4.1.1 or earlier

# Linux
ln -s "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" src\io_scene_vrm
```

## To run the code format, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. double-click `tools\format.bat` in the repository to run it.

## To run the code format in Visual Studio Code, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. in the Visual Studio Code terminal, run the `uv sync` command.
3. run Visual Studio Code's `Format Document`.

The same result can be achieved by using the `Ruff` extension of Visual Studio Code.

## To run the code type check, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. double-click `tools\lint.bat` in the repository and run it.

## To run the type checking of the code in Visual Studio Code, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. in the Visual Studio Code terminal, run the `uv sync` command.
3. install `Ruff`, `Mypy Type Checker` and `Pylance` extensions in Visual Studio Code.
4. open the py file you want to type check.

## To run the software test of the code, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. double-click `tools\test.bat` in the repository and run it.
3. if you get the error `Blender not found`, set the environment variable `BLENDER_VRM_TEST_BLENDER_PATH` to the path of the Blender 4.2 or 3.6 or 3.3 or 2.93 exe file.

## To run the software test of the code in Visual Studio Code, follow these steps

1. install [astral-sh/uv](https://docs.astral.sh/uv/).
2. in the Visual Studio Code terminal, run the `uv sync` command.
3. select `Testing` from the left icon in Visual Studio Code
4. select `Configure Python Tests.
5. select `unittests` as the test library.
6. select `Root Directory` as test folder.
7. select `test_*` as test file pattern.
8. press `Run Tests`
9. if you get the error `Blender not found`, set the environment variable `BLENDER_VRM_TEST_BLENDER_PATH` to the path of the Blender 4.2 or 3.6 or 3.3 or 2.93 exe file.
