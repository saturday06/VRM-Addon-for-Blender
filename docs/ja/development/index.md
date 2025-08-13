---
title: '開発環境のセットアップ'
---

[GitHubレポジトリ](https://github.com/saturday06/VRM-Addon-for-Blender)には本体のソースコード、
コードフォーマット設定、型チェック設定、ソフトウェアテスト設定が含まれています。
これらは [astral-sh/uv](https://docs.astral.sh/uv/)に強く依存しているので、
まずそれをインストールする必要があります。 あるいは
[Dev Container](https://containers.dev/)
を使って全自動で設定することもできます。

## Blenderのアドオンフォルダにレポジトリにリンクする

GitHubレポジトリ内の
[src/io_scene_vrm](https://github.com/saturday06/VRM-Addon-for-Blender/tree/main/src/io_scene_vrm)
フォルダがアドオン本体です。そのフォルダへのリンクをBlenderの `user_default`
あるいは `addons` フォルダ内に作ることで、
開発中のソースコードをBlenderにアドオンとしてインストールした扱いにすることができ、
効率的に動作確認をすることができるようになります。

### Blender 4.2以上向けの、開発用リンクの作成方法

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

### Blender 4.2未満向けの、開発用リンクの作成方法

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

## コードフォーマットの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\format.bat` をダブルクリックして実行する。

## Visual Studio Codeでのコードフォーマットの実行方法

1. Visual Studio Code の `Ruff` 拡張機能をインストールする。
2. Visual Studio Code の `Format Document` を実行する。

## 型チェックの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\lint.bat` をダブルクリックして実行する。

## Visual Studio Codeでの型チェックの実行方法

1. Visual Studio Code の `Pyright` 拡張機能をインストールする。
2. 型チェックをしたい py ファイルを開く。

## ソフトウェアテストの実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. リポジトリの `tools\test.bat` をダブルクリックして実行する。

## Visual Studio Codeでのソフトウェアテストを実行方法

1. [astral-sh/uv](https://docs.astral.sh/uv/) をインストールする。
2. Visual Studio Code のターミナルで `uv sync` コマンドを実行する。
3. Visual Studio Code の左のアイコンから `Testing` を選択する。
4. `Configure Python Tests` を選択する。
5. テストライブラリとして `unittests` を選択する。
6. テストフォルダとして `Root Directory` を選択する。
7. テストファイルパターンとして `test_*` を選択する。
8. `Run Tests` を押す。
