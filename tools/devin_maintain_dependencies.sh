#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")/.."

sudo ./tools/install_ubuntu_packages.sh

if ! command -v uv; then
  curl --fail --show-error --location https://astral.sh/uv/install.sh | sh
fi

if ! command -v deno; then
  # https://github.com/denoland/deno/issues/25931#issuecomment-2406073767
  curl --fail --show-error --location https://deno.land/install.sh | sh -s -- --yes
  # deno doesn't add a newline to the last line of .bashrc, so we add it ourselves.
  echo >>~/.bashrc
fi

bash -lc ./tools/devcontainer_update_content_command.sh
bash -lc ./tools/devcontainer_post_attach_command.sh
