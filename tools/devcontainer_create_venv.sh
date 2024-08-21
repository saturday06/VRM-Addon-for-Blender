#!/bin/bash

set -eu -o pipefail

if [ ! -e .venv ]; then
  if [ "$(uname -m)" = "x86_64" ]; then
    uv venv --prompt venv
  else
    # x86_64以外の場合はbpyパッケージが存在しないので、システムのものを使う
    uv venv --prompt venv --python /usr/local/bin/python3 --system-site-packages
  fi
fi

# 環境によってはパッケージのインストールは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if uv run python -c ''; then # パッケージのインストールを実行
    break
  fi
  sleep 10
done
