#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

create_venv() (
  if [ "$(uname -m)" = "x86_64" ]; then
    uv venv --prompt venv
  else
    # x86_64以外の場合はbpyパッケージが存在しないので、システムのものを使う
    uv venv --prompt venv --python /usr/local/bin/python3 --system-site-packages
  fi
)

create=yes

if [ "$(uname -m)" = "x86_64" ]; then
  if grep -E "^home = /home/developer/.local/share/uv/python/" .venv/pyvenv.cfg >/dev/null &&
    readlink -e .venv/bin/python >/dev/null \
    ; then
    create=no
  fi
else
  if grep -E "^home = /usr/local/bin$" .venv/pyvenv.cfg >/dev/null &&
    grep -E "^include-system-site-packages = true$" .venv/pyvenv.cfg >/dev/null &&
    readlink -e .venv/bin/python >/dev/null \
    ; then
    create=no
  fi
fi

if ([ "$create" = "yes" ] && ! create_venv) || ! uv run --isolated -- python -c ""; then
  if ! sudo rm -fr .venv; then
    # Docker for Windowsバックエンド切り替え時などに消せないファイルが残ることがある
    echo >&2 # ログ表示成形のため改行出力
    echo >&2 "####################################################"
    echo >&2 "Failed to remove '.venv'. Please remove it manually."
    echo >&2 "####################################################"
    exit 1
  fi
  create_venv
fi

# 環境によってはパッケージのインストールは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if uv sync --reinstall-package starry-bpy-typings; then
    break
  fi
  sleep 10
done
