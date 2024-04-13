#!/bin/bash

set -eu -o pipefail

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo apt-get update
sudo apt-get dist-upgrade --yes

./tools/devcontainer_fixup_workspace.sh

# 空のvenvを作る。
poetry run python -c ""

# poetry 1.8.2が自動で作るvenvのスクリプトをVSCodeのターミナルが正しく解釈できないので手動で作る。
# 例えばvenvの名前が "venv" で、シェルのデフォルトのプロンプトが "$" の場合、シェルのプロンプトは
# 正しくは "(venv) $" となるべきだが、現状のpoetryとVSCodeの組み合わせでは "venv$" になっている。
if [ "$(uname -m)" = "x86_64" ]; then
  /usr/local/bin/python3 -m venv "$(poetry env info --path)" --clear --prompt venv
else
  /usr/local/bin/python3 -m venv "$(poetry env info --path)" --clear --prompt venv --system-site-packages
fi

poetry completions bash >>~/.bash_completion

# いちおうサブモジュールを取得するが、作業フォルダの状態次第で失敗するので `|| true` を付与
git submodule update --init --recursive || true

# 環境によってはpoetry installは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if poetry install; then
    break
  fi
done

# システムのBlenderから開発中のアドオンをすぐに動作確認できるようにする
for blender_version in \
  4.3 \
  4.2 \
  4.1 \
  4.0 \
  3.6 \
  3.5 \
  3.4 \
  3.3 \
  3.2 \
  3.1 \
  3.0 \
  2.93; do
  mkdir -p "$HOME/.config/blender/$blender_version/scripts/addons"
  ln -fs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/scripts/addons/"
done
