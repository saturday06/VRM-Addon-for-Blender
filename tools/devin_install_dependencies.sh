#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

cd "$(dirname "$0")/.."

cat <<'BASHRC' >>~/.bashrc
export PATH="/home/developer/.deno/bin:/home/developer/.cargo/bin:/home/developer/.local/bin:$PATH"
BASHRC

./tools/devin_maintain_dependencies.sh
