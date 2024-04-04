#!/bin/bash

set -eu -o pipefail

# 作業フォルダの所有者やパーミッションを設定する。
# sudoが強力すぎるため、poetryは経由せずOSのパッケージのみを用いて実行する。
sudo env PYTHONDONTWRITEBYTECODE=1 ./tools/devcontainer_fixup_files.py

# いちおうサブモジュールを取得するが、作業フォルダの状態次第で失敗するので `|| true` を付与
git submodule update --init --recursive || true

./tools/install_hugo.sh
./tools/install_hadolint.sh

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false

# 環境によってはpoetry installは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if poetry install; then
    break
  fi
done
