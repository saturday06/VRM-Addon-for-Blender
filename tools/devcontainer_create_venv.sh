#!/bin/bash

set -eu -o pipefail

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false

# x86_64以外の場合はbpyパッケージが存在しないので、システムのものを使う
[ "$(uname -m)" = "x86_64" ] || poetry config virtualenvs.options.system-site-packages true

# .venv-devcontainerをvenvとした使う
if [ -L .venv-devcontainer ] ||
  [ ! -e .venv-devcontainer ] ||
  [ ! -e "$(poetry env info --path)" ] ||
  [ "$(readlink --canonicalize-existing .venv-devcontainer)" != "$(readlink --canonicalize-existing "$(poetry env info --path)")" ] \
  ; then

  if ! sudo rm -fr .venv-devcontainer; then
    # Docker for Windowsバックエンド切り替え時などに消せないファイルが残ることがある
    echo >&2 # ログ表示成形のため改行出力
    echo >&2 "#################################################################"
    echo >&2 "Failed to remove '.venv-devcontainer'. Please remove it manually."
    echo >&2 "#################################################################"
    exit 1
  fi

  # poetry 1.8.2が自動で作るvenvのスクリプトをVSCodeのターミナルが正しく解釈できないので手動で作る。
  # 例えばvenvの名前が "venv" で、シェルのデフォルトのプロンプトが "$" の場合、シェルのプロンプトは
  # 正しくは "(venv) $" となるべきだが、現状のpoetryとVSCodeの組み合わせでは "venv$" になっている。
  if [ "$(uname -m)" = "x86_64" ]; then
    /usr/local/bin/python3 -m venv .venv-devcontainer --prompt venv
  else
    # x86_64以外の場合はbpyパッケージが存在しないので、システムのものを使う
    /usr/local/bin/python3 -m venv .venv-devcontainer --prompt venv --system-site-packages
  fi

  # poetry内部のvenvのパスを得るため、仮のvenvが無い場合は空のpythonコマンドを実行して作る
  poetry run python -c ""
  # 内部のvenvから.venv-devcontainerにリンクを貼る
  poetry_venv_path=$(poetry env info --path)
  mkdir -p .venv-devcontainer "$(dirname "$poetry_venv_path")"
  if [ "$(readlink -f "$poetry_venv_path")" != "$(readlink -f "$PWD/.venv-devcontainer")" ]; then
    sudo rm -fr "$poetry_venv_path"
    ln -fsv "$PWD/.venv-devcontainer" "$poetry_venv_path"
  fi

  # 環境によってはpoetry installは5%くらいの頻度で失敗するのでリトライする
  for _ in $(seq 5); do
    if poetry install; then
      break
    fi
    sleep 10
  done
fi
