---
title: "開発環境のセットアップ"
---

このリポジトリには、コードフォーマット設定、型チェック設定、ソフトウェアテスト設定が含まれています。

これらは [astral-sh/uv](https://docs.astral.sh/uv/) に強く依存しているので、まずそれをインストールする必要があります。あるいは、Visual Studio Codeのdevcontainerを使って全自動で設定することもできます。

## Blenderのアドオンフォルダにレポジトリにリンクする

開発用のソースコードは [main](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main) ブランチにあります。ブランチ内の [src/io_scene_vrm](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm) フォルダがアドオン本体です。
そのフォルダへのリンクをBlenderの `addons` フォルダ内に作ることで効率的に開発をすることができます。

```text
# レポジトリのセットアップ
git checkout main

# Blender 4.2以上の場合

# Linux
ln -s "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/extensions/user_default/vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/extensions/user_default/vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\extensions\user_default\vrm" src\io_scene_vrm

# Blender 4.2未満の場合

# Linux
ln -s "$PWD/src/io_scene_vrm" "$HOME/.config/blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# macOS
ln -s "$PWD/src/io_scene_vrm" "$HOME/Library/Application Support/Blender/BLENDER_VERSION/scripts/addons/io_scene_vrm"
# Windows PowerShell
New-Item -ItemType Junction -Path "$Env:APPDATA\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" -Value "$(Get-Location)\src\io_scene_vrm"
# Windows Command Prompt
mklink /j "%APPDATA%\Blender Foundation\Blender\BLENDER_VERSION\scripts\addons\io_scene_vrm" src\io_scene_vrm
```

## コードフォーマットの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\format.bat` をダブルクリックして実行する。

## Visual Studio Codeでのコードフォーマットの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. Visual Studio Code のターミナルで `uv sync` コマンドを実行する。
3. Visual Studio Code の `Format Document` を実行する。

Visual Studio Code の `Ruff` 拡張機能を使っても同じ結果が得られる。

## 型チェックの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\lint.bat` をダブルクリックして実行する。

## Visual Studio Codeでの型チェックの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. Visual Studio Code のターミナルで `uv sync` コマンドを実行する。
3. Visual Studio Code に `Ruff`、`Mypy Type Checker`、`Pylance` 拡張をインストールする。
4. タイプチェックをしたい py ファイルを開く。

## ソフトウェアテストの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\test.bat` をダブルクリックして実行する。
3. Blenderが見つからないという趣旨のエラーが表示されたら、環境変数 `BLENDER_VRM_TEST_BLENDER_PATH` に Blender 4.2 または 3.6 または 3.3 または 2.93 の exe ファイルのパスを設定する。

## Visual Studio Codeでのソフトウェアテストを実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. Visual Studio Code のターミナルで `uv sync` コマンドを実行する。
3. Visual Studio Code の左のアイコンから `Testing` を選択する。
4. `Configure Python Tests` を選択する。
5. テストライブラリとして `unittests` を選択する。
6. テストフォルダとして `Root Directory` を選択する。
7. テストファイルパターンとして `test_*` を選択する。
8. `Run Tests` を押す。
9. `Blender not found` というエラーが表示されたら、環境変数 `BLENDER_VRM_TEST_BLENDER_PATH` に Blender 4.2 または 3.6 または 3.3 または 2.93 の exe ファイルのパスを設定する。
