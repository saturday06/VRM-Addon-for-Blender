# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
FROM ubuntu:24.04@sha256:c35e29c9450151419d9448b0fd75374fec4fff364a27f176fb458d472dfc9e54

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN --mount=type=bind,source=.,target=/root/src/tools <<'INSTALL_PACKAGES'
  set -eu

  /root/src/tools/install_ubuntu_packages.sh

  # https://github.com/cli/cli/blob/v2.65.0/docs/install_linux.md#debian-ubuntu-linux-raspberry-pi-os-apt
  curl --fail --show-error --location --output /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gh=*

  apt-get dist-clean
  rm -rf /var/lib/apt/lists/*
INSTALL_PACKAGES

RUN <<'SETUP_USER_DEVELOPER'
  set -eu
  useradd --create-home --user-group --shell /bin/bash developer
  echo "developer ALL=(root) NOPASSWD:ALL" | tee /etc/sudoers.d/developer
  mkdir -p /workspace
  chown developer:developer /workspace
SETUP_USER_DEVELOPER

USER developer
WORKDIR /home/developer

RUN <<'SETUP_USER_DEVELOPER_LOCAL_ENVIRONMENT'
  set -eu

  cat <<'SHELL_PROFILE_SCRIPT' | tee -a ~/.profile ~/.bash_profile ~/.bashrc ~/.zshrc
export BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
export DISPLAY=:0
export UV_LINK_MODE=copy
SHELL_PROFILE_SCRIPT

  mkdir -p ~/.vnc
  cat <<'VNC_XSTARTUP_SCRIPT' >>~/.vnc/xstartup
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
tint2 &
xterm &
(while sleep 1; do xterm -e blender --python-expr "import debugpy; debugpy.listen(5678)" --open-last || true; done) &
exec openbox-session
VNC_XSTARTUP_SCRIPT
  chmod +x ~/.vnc/xstartup

  mkdir -p Desktop Documents Downloads Music Pictures Videos
  # https://docs.astral.sh/uv/getting-started/installation/
  curl --fail --show-error --location https://astral.sh/uv/install.sh | sh

  # https://github.com/denoland/deno/issues/25931#issuecomment-2406073767
  curl --fail --show-error --location https://deno.land/install.sh | sh -s -- --yes
  # Deno doesnot add newlines to the final line of shell config, so add them manually.
  echo | tee -a ~/.profile ~/.bash_profile ~/.bashrc ~/.zshrc
SETUP_USER_DEVELOPER_LOCAL_ENVIRONMENT
