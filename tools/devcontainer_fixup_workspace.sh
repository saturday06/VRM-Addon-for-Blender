#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

# 作業フォルダの所有者やパーミッションを設定する。
# sudoが強力すぎるため、uvは経由せずOSのパッケージのみを用いて実行する。
sudo env PYTHONDONTWRITEBYTECODE=1 ./tools/devcontainer_fixup_workspace_files.py

./tools/devcontainer_create_venv.sh
