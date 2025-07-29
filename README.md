<a name="en" />

[ English / [日本語](#ja_JP) ]

# KHR Avatar/VRM Add-on for Blender [![CI status](https://github.com/saturday06/VRM-Addon-for-Blender/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/saturday06/VRM-Addon-for-Blender/actions) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Import, export, and editing functions for VRM format and experimental KHR avatar
format.

## Download

- For Blender 4.2 or later:
  [🛠️**Blender Extensions Platform**](https://extensions.blender.org/add-ons/vrm).
- For Blender 2.93 to 4.1:
  [🌐**The Official Site**](https://vrm-addon-for-blender.info).

## Tutorials

|                                         [Installation](https://vrm-addon-for-blender.info/en/installation?locale_redirection)                                          |                                    [Create Simple VRM](https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection)                                    |                                    [Create Humanoid VRM](https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection)                                    |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| <a href="https://vrm-addon-for-blender.info/en/installation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/installation.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/simple.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/humanoid.gif"></a> |
|                               **[Create Physics Based Material](https://vrm-addon-for-blender.info/en/material-pbr?locale_redirection)**                               |                                     **[Create Anime Style Material](https://vrm-addon-for-blender.info/en/material-mtoon?locale_redirection)**                                     |                                      **[Automation with Python Scripts](https://vrm-addon-for-blender.info/en/scripting-api?locale_redirection)**                                      |
| <a href="https://vrm-addon-for-blender.info/en/material-pbr?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/material_pbr.gif"></a> |     <a href="https://vrm-addon-for-blender.info/en/material-mtoon?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/material_mtoon.gif"></a>     |        <a href="https://vrm-addon-for-blender.info/en/scripting-api?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/scripting_api.gif"></a>        |
|                                        **[VRM Animation](https://vrm-addon-for-blender.info/en/animation?locale_redirection)**                                         |                                           **[Development How-To](https://vrm-addon-for-blender.info/en/development?locale_redirection)**                                           |                                                                                                                                                                                        |
|    <a href="https://vrm-addon-for-blender.info/en/animation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/animation.gif"></a>    |         <a href="https://vrm-addon-for-blender.info/en/development?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/animation.gif"></a>         |                                                                                                                                                                                        |

## Overview

This add-on adds VRM-related functions to Blender, such as importing and
exporting VRM, adding VRM Humanoid and setting MToon shaders. Bug reports,
feature requests, pull requests, and contributions are welcome. I have taken
over the development after
[Version 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79)
from the author, [@iCyP](https://github.com/iCyP).

## Development

The source code for development is in the
[`main`](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main) branch.
Its
[`src/io_scene_vrm`](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm)
folder is a main body of the add-on. For efficient development, you can create a
link to that folder in the Blender `addons` folder.

For more advanced development, such as running tests, please use
[astral.sh/uv](https://docs.astral.sh/uv/). See
[the tutorial](https://vrm-addon-for-blender.info/en/development?locale_redirection)
for more information.

```text
git checkout main

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

---

<a name="ja_JP" />

[ [English](#en) / 日本語 ]

# KHR Avatar/VRM Add-on for Blender [![CI status](https://github.com/saturday06/VRM-Addon-for-Blender/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/saturday06/VRM-Addon-for-Blender/actions) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

BlenderにVRM関連機能と実験的なKHR Avatar関連機能を追加するアドオンです。

## ダウンロード

- Blender 4.2以上をお使いの場合:
  [🛠️**Blender Extensions Platform**](https://extensions.blender.org/add-ons/vrm)
- Blender 2.93から4.1をお使いの場合:
  [🌐**オフィシャルWebサイト**](https://vrm-addon-for-blender.info)

## チュートリアル

|                                       [インストール方法](https://vrm-addon-for-blender.info/en/installation?locale_redirection)                                        |                                   [シンプルなVRMを作る](https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection)                                   |                                      [人型のVRMを作る](https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection)                                      |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| <a href="https://vrm-addon-for-blender.info/en/installation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/installation.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-simple-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/simple.gif"></a> | <a href="https://vrm-addon-for-blender.info/en/create-humanoid-vrm-from-scratch?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/humanoid.gif"></a> |
|                                **[物理ベースのマテリアル設定](https://vrm-addon-for-blender.info/ja/material-pbr?locale_redirection)**                                 |                                      **[アニメ風のマテリアル設定](https://vrm-addon-for-blender.info/ja/material-mtoon?locale_redirection)**                                       |                                       **[Pythonスクリプトによる自動化](https://vrm-addon-for-blender.info/en/scripting-api?locale_redirection)**                                       |
| <a href="https://vrm-addon-for-blender.info/en/material-pbr?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/material_pbr.gif"></a> |     <a href="https://vrm-addon-for-blender.info/en/material-mtoon?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/material_mtoon.gif"></a>     |        <a href="https://vrm-addon-for-blender.info/en/scripting-api?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/scripting_api.gif"></a>        |
|                                      **[VRMアニメーション](https://vrm-addon-for-blender.info/en/animation?locale_redirection)**                                       |                                             **[改造するには?](https://vrm-addon-for-blender.info/en/development?locale_redirection)**                                              |                                                                                                                                                                                        |
|    <a href="https://vrm-addon-for-blender.info/en/animation?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/animation.gif"></a>    |         <a href="https://vrm-addon-for-blender.info/en/development?locale_redirection"><img width="200" src="https://vrm-addon-for-blender.info/images/animation.gif"></a>         |                                                                                                                                                                                        |

## 概要

BlenderにVRMのインポートやエクスポート、VRM
Humanoidの追加やMToonシェーダーの設定などのVRM関連機能を追加するアドオンです。バグ報告、機能要望、Pull
Request等歓迎します。[バージョン 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79)以降の開発を作者である[@iCyP](https://github.com/iCyP)さんから引き継ぎました。

## 改造するには

開発用のソースコードは
[`main`](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main)ブランチにあります。ブランチ内の
[`src/io_scene_vrm`](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm)
フォルダがアドオン本体です。 そのフォルダへのリンクをBlenderの `addons`
フォルダ内に作ることで効率的に開発をすることができます。

テストの実行など、より高度な開発をする場合は[astral.sh/uv](https://docs.astral.sh/uv/)をご利用ください。詳しい情報は[チュートリアル](https://vrm-addon-for-blender.info/en/development?locale_redirection)にあります。

```text
git checkout main

# Blender 4.2以上の場合

# Linux
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/extensions/user_default/vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/extensions/user_default/vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" src\io_scene_vrm

# Blender 4.2未満の場合

# Linux
ln -Ts "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" src\io_scene_vrm
```

..
