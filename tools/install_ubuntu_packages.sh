#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install \
  advancecomp \
  blender \
  curl \
  dbus-x11 \
  diffutils \
  ffmpeg \
  file \
  git \
  git-lfs \
  gnupg \
  imagemagick \
  less \
  libsm6 \
  libxi6 \
  libxkbcommon0 \
  moreutils \
  netcat-openbsd \
  nkf \
  novnc \
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
  tigervnc-standalone-server \
  uchardet \
  unzip \
  websockify \
  openbox \
  xterm \
  xz-utils \
  xxd \
  zopfli \
  -y --no-install-recommends
