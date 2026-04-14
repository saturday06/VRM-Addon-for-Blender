#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

install_ubuntu_vnc_packages() (
  timeout 5m apt-get update -qq || exit 1
  DEBIAN_FRONTEND=noninteractive timeout 15m apt-get install \
    blender \
    build-essential \
    dbus-x11 \
    libxi6 \
    libxkbcommon0 \
    novnc \
    openbox \
    tigervnc-standalone-server \
    tint2 \
    websockify \
    xterm \
    xvfb \
    -y --no-install-recommends ||
    exit 1
)

for retry in $(seq 5 -1 0); do
  if install_ubuntu_vnc_packages; then
    break
  fi

  if [ "$retry" -eq 0 ]; then
    >&2 echo "Failed to install ubuntu vnc packages"
    exit 1
  fi

  sleep 300
done
