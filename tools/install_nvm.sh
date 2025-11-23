#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

nvm_installer_url="https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh"
if command -v curl; then
  curl \
    --fail \
    --show-error \
    --location \
    --retry 20 \
    --retry-all-errors \
    --output install_nvm.tmp.sh \
    "$nvm_installer_url"
else
  wget \
    --tries=20 \
    --retry-connrefused \
    --retry-on-host-error \
    --output-document=install_nvm.tmp.sh \
    "$nvm_installer_url"
fi
bash install_nvm.tmp.sh
rm install_nvm.tmp.sh
