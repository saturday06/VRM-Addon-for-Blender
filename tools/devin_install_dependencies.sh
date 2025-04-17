#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")/.."

cat <<'BASHRC' >>~/.bashrc
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
BASHRC

./tools/devin_maintain_dependencies.sh
