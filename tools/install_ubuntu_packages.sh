#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

install_ubuntu_packages() (
  timeout 5m apt-get update -qq || exit 1
  DEBIAN_FRONTEND=noninteractive timeout 15m apt-get install \
    advancecomp \
    blender \
    build-essential \
    curl \
    dbus-x11 \
    diffutils \
    ffmpeg \
    file \
    git \
    gnupg \
    imagemagick \
    less \
    libsm6 \
    libxi6 \
    libxkbcommon0 \
    lsb-release \
    moreutils \
    netcat-openbsd \
    nkf \
    novnc \
    openbox \
    patchutils \
    python3-debugpy \
    python3-numpy \
    python3-pygit2 \
    python3-tqdm \
    python3-typing-extensions \
    ruby \
    ruby-rmagick \
    shellcheck \
    shfmt \
    sudo \
    tigervnc-standalone-server \
    tint2 \
    uchardet \
    unzip \
    websockify \
    xterm \
    xvfb \
    xxd \
    xz-utils \
    zopfli \
    -y --no-install-recommends ||
    exit 1
)

for retry in $(seq 5 -1 0); do
  if install_ubuntu_packages; then
    break
  fi

  if [ "$retry" -eq 0 ]; then
    >&2 echo "Failed to install ubuntu packages"
    exit 1
  fi

  sleep 300
done
