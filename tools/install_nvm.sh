#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

# https://github.com/nvm-sh/nvm/blob/v0.40.3/README.md?plain=1#L117-L118
if ! command -v nvm; then
  cat <<'NVM_SHELL_CONFIG' | tee -a ~/.bash_profile ~/.bashrc ~/.zshrc ~/.profile
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
NVM_SHELL_CONFIG
fi

# https://github.com/nvm-sh/nvm/blob/v0.40.3/README.md?plain=1#L107
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

bash -lc "nvm install"
