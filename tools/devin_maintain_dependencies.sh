#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")/.."

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install \
  advancecomp \
  blender \
  curl \
  diffutils \
  file \
  git \
  git-lfs \
  imagemagick \
  less \
  libsm6 \
  libxi6 \
  libxkbcommon0 \
  moreutils \
  nkf \
  patchutils \
  python3-dulwich \
  python3-numpy \
  python3-tqdm \
  python3-typing-extensions \
  ruby \
  shellcheck \
  sudo \
  unzip \
  xz-utils \
  zopfli \
  -y

if ! command -v uv; then
  curl --fail --show-error --location https://astral.sh/uv/install.sh | sh
fi

if ! command -v deno; then
  # https://github.com/denoland/deno/issues/25931#issuecomment-2406073767
  curl --fail --show-error --location https://deno.land/install.sh | sh -s -- --yes
  # denoは.bashrcの最終行に改行を追加しないので自前で追加する。
  echo >>~/.bashrc
fi

bash -lc ./tools/devcontainer_on_create_command.sh
bash -lc ./tools/devcontainer_update_content_command.sh
bash -lc ./tools/devcontainer_post_attach_command.sh
