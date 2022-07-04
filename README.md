# VRM Add-on for Blender <a href="https://github.com/saturday06/VRM_Addon_for_Blender/actions"><img alt="CI status" src="https://github.com/saturday06/VRM_Addon_for_Blender/actions/workflows/test.yml/badge.svg?branch=main"></a> <a href="https://github.com/psf/black"><img alt="Code style is black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
## 概要
BlenderにVRM関連機能を追加するアドオンです。

## ダウンロード
[Webサイト](https://vrm-addon-for-blender.info)

## 更新について
アップデートの際は古いアドオンを削除してください。  
2021年2月7日のリリースでアドオン名(旧名:VRM_IMPORTER_for_Blender)と[インストール方法](https://vrm-addon-for-blender.info/en/installation?locale_redirection)を変更したためです。

## チュートリアル

| [インストール方法](https://vrm-addon-for-blender.info/en/installation?locale_redirection) | [単純なVRMを作る](https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection) | [人型のVRMを作る](https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection) |
| :---: | :---: | :---: |
| <a href="https://vrm-addon-for-blender.info/en/installation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/en/images/installation.png"></a> | <a href="https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/simple.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/humanoid.gif"></a> |

## 開発するには

開発用のソースコードは<a href="https://github.com/saturday06/VRM_Addon_for_Blender/tree/main">`main`</a>ブランチにあります。ブランチ内の <a href="https://github.com/saturday06/VRM_Addon_for_Blender/tree/main/io_scene_vrm">`io_scene_vrm`</a> フォルダがBlenderアドオン本体です。  
`io_scene_vrm` フォルダへのリンクをBlenderの `addons` フォルダ内に作ることで効率的に開発をすることができます。

テストの実行などより高度な開発をする場合は[Poetry](https://python-poetry.org/)をご利用ください。

```
git checkout main
git submodule update --init

# Linux
ln -s "$PWD/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/VRM_Addon_for_Blender-repo"
# macOS
ln -s "$PWD/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/VRM_Addon_for_Blender-repo"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\VRM_Addon_for_Blender-repo" -Value "$(Get-Location)\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\VRM_Addon_for_Blender-repo" io_scene_vrm
```

# VRM Add-on for Blender <a href="https://github.com/saturday06/VRM_Addon_for_Blender/actions"><img alt="CI status" src="https://github.com/saturday06/VRM_Addon_for_Blender/actions/workflows/test.yml/badge.svg?branch=main"></a> <a href="https://github.com/psf/black"><img alt="Code style is black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Overview
VRM Add-on for Blender is the add-on to add VRM-related functions into Blender.

## Download
[Website](https://vrm-addon-for-blender.info)

## Updating
Please remove the old add-on when it update.  
It is because the release on February 7, 2021 changed the add-on name from (ex-VRM_IMPORTER_for_Blender) and changed the [installation method](https://vrm-addon-for-blender.info/en/installation?locale_redirection).

## Tutorials

| [Installation](https://vrm-addon-for-blender.info/en/installation?locale_redirection) | [Create Simple VRM](https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection) | [Create Humanoid VRM](https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection) |
| :---: | :---: | :---: |
| <a href="https://vrm-addon-for-blender.info/en/installation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/en/images/installation.png"></a> | <a href="https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/simple.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/humanoid.gif"></a> |

## Development

The source code for development is in the <a href="https://github.com/saturday06/VRM_Addon_for_Blender/tree/main">`main`</a> branch. Its <a href="https://github.com/saturday06/VRM_Addon_for_Blender/tree/main/io_scene_vrm">`io_scene_vrm`</a> folder is the main body of the Blender add-on. For efficient development, you can create a link to that folder in the Blender `addons` folder.

For more advanced development, such as running tests, please use [Poetry](https://python-poetry.org/).

```
git checkout main
git submodule update --init

# Linux
ln -s "$PWD/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/VRM_Addon_for_Blender-repo"
# macOS
ln -s "$PWD/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/VRM_Addon_for_Blender-repo"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\VRM_Addon_for_Blender-repo" -Value "$(Get-Location)\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\VRM_Addon_for_Blender-repo" io_scene_vrm
```
