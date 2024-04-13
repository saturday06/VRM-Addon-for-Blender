#!/bin/bash

set -eu -o pipefail

# 作業フォルダの所有者やパーミッションを設定する。
# sudoが強力すぎるため、poetryは経由せずOSのパッケージのみを用いて実行する。
sudo env PYTHONDONTWRITEBYTECODE=1 ./tools/devcontainer_fixup_workspace_files.py

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false

# x86_64以外の場合はbpyパッケージが存在しないので、システムのものを使う
[ "$(uname -m)" = "x86_64" ] || poetry config virtualenvs.options.system-site-packages true
