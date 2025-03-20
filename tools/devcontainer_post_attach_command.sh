#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

./tools/devcontainer_create_venv.sh

sudo systemctl enable --now docker

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status --short
