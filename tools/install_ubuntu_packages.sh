#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install \
  advancecomp \
  blender \
  curl \
  diffutils \
  ffmpeg \
  file \
  fonts-noto \
  git \
  git-lfs \
  gnupg \
  imagemagick \
  less \
  libsm6 \
  libxi6 \
  libxkbcommon0 \
  moreutils \
  nkf \
  patchutils \
  python3-pygit2 \
  python3-numpy \
  python3-tqdm \
  python3-typing-extensions \
  ruby \
  shellcheck \
  shfmt \
  sudo \
  supervisor \
  uchardet \
  unzip \
  xdotool \
  xorgxrdp \
  xubuntu-desktop \
  xrdp \
  xz-utils \
  zopfli \
  -y --no-install-recommends
