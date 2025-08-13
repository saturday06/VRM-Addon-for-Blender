---
title: 'Development How-To'
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
folder contains the main add-on code. By creating a symbolic link to this folder
in Blender's `user_default` or `addons` directory, you can install the
development source code as an add-on in Blender, making it easy to test changes
efficiently.

### How to create a development link for Blender 4.2 or later

#### Linux

```sh
blender_version=4.5
mkdir -p "$HOME/.config/blender/$blender_version/extensions/user_default"
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/extensions/user_default/vrm"
```

#### macOS

```sh
blender_version=4.5
mkdir -p "$HOME/Library/Application Support/Blender/$blender_version/extensions/user_default"
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/$blender_version/extensions/user_default/vrm"
```

#### Windows PowerShell

```powershell
$blenderVersion = 4.5
New-Item -ItemType Directory -Path "$Env:APPDATA\Blender Foundation\Blender\$blenderVersion\extensions\user_default" -Force
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\$blenderVersion\extensions\user_default\vrm" -Value "$(Get-Location)\src\io_scene_vrm"
```

### How to create a development link for Blender 4.1.1 or earlier

#### Linux

```sh
blender_version=4.5
mkdir -p "$HOME/.config/blender/$blender_version/scripts/addons"
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/scripts/addons/io_scene_vrm"
```

#### macOS

```sh
blender_version=4.5
mkdir -p "$HOME/Library/Application Support/Blender/$blender_version/scripts/addons"
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/$blender_version/scripts/addons/io_scene_vrm"
```

#### Windows PowerShell

```powershell
$blenderVersion = 4.5
New-Item -ItemType Directory -Path "$Env:APPDATA\Blender Foundation\Blender\$blenderVersion\scripts\addons" -Force
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\$blenderVersion\scripts\addons\io_scene_vrm" -Value "$(Get-Location)\src\io_scene_vrm"
```

## To format the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\format.bat` in the repository to run it.

## To format the code in Visual Studio Code, follow these steps

1. Install the `Ruff` extension in Visual Studio Code.
2. Run Visual Studio Code's `Format Document`.

## To run type checking of the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\lint.bat` in the repository and run it.

## To run type checking of the code in Visual Studio Code, follow these steps

1. Install the `Pyright` extension in Visual Studio Code.
2. Open the Python file you want to type check.

## To run the software tests of the code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. Double-click `tools\test.bat` in the repository and run it.

## To run the software tests of the code in Visual Studio Code, follow these steps

1. Install [astral-sh/uv](https://docs.astral.sh/uv/).
2. In the Visual Studio Code terminal, run the `uv sync` command.
3. Select `Testing` from the left icon in Visual Studio Code.
4. Select `Configure Python Tests`.
5. Select `unittests` as the test library.
6. Select `Root Directory` as the test folder.
7. Select `test_*` as the test file pattern.
8. Press `Run Tests`.
