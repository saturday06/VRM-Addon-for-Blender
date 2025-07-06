#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

curl \
  --fail \
  --show-error \
  --location \
  --retry 20 \
  --retry-all-errors \
  --output install_nvm.tmp.sh \
  https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh
bash install_nvm.tmp.sh
rm install_nvm.tmp.sh
