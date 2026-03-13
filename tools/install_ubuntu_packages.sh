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
  -y --no-install-recommends

# https://github.com/docker/docs/blob/eca493b8107b096369bac919367b0d74cfd32786/content/manuals/engine/install/ubuntu.md#install-using-the-apt-repository-install-using-the-repository
if ! command -v docker; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  ubuntu_codename=$(lsb_release --codename --short)
  tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${ubuntu_codename}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin \
    -y --no-install-recommends
fi
