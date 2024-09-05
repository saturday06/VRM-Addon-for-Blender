#!/bin/bash

set -eu -o pipefail

# WindowsのHyper-Vバックエンドだと、rootユーザーだと現在のディレクトリの所有者を変更できないことがある。
# たとえば 'sudo chown -v .'' コマンドを実行すると下記の出力になって成功表示になる。
# > changed ownership of '/workspaces/VRM-Addon-for-Blender/' from root:root to developer:developer
# しかし、その後lsコマンドなどでパーミッションを確認するとroot:rootに戻っている。
# なぜかsudoをつけないで実行すると正しく所有者の変更ができる。
# 所有者が正しくなっていないとgitコマンドがエラーになり致命的なので、特別にこのフォルダだけ個別に所有者変更を行う。
# 通常の所有者やパーミッションの変更処理は tools/devcontainer_update_content_command.sh で行うようにする。
chown developer:developer . || true

./tools/devcontainer_create_venv.sh

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status --short
