# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
FROM ubuntu:24.04

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN <<'INSTALL_PACKAGES'
  set -eu

  apt-get update
  apt-get install \
    advancecomp=* \
    blender=* \
    curl=* \
    diffutils=* \
    ffmpeg=* \
    file=* \
    git=* \
    git-lfs=* \
    gnupg=* \
    imagemagick=* \
    less=* \
    libsm6=* \
    libxi6=* \
    libxkbcommon0=* \
    moreutils=* \
    nkf=* \
    patchutils=* \
    python3-pygit2=* \
    python3-numpy=* \
    python3-tqdm=* \
    python3-typing-extensions=* \
    ruby=* \
    shellcheck=* \
    shfmt=* \
    sudo=* \
    unzip=* \
    xz-utils=* \
    zopfli=* \
    -y --no-install-recommends

  # https://github.com/cli/cli/blob/v2.65.0/docs/install_linux.md#debian-ubuntu-linux-raspberry-pi-os-apt
  curl --fail --show-error --location --output /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  apt-get update
  apt-get install gh=* -y --no-install-recommends

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

  cat <<'SHELL_PROFILE_SCRIPT' >>~/.profile
export BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
export UV_LINK_MODE=copy
SHELL_PROFILE_SCRIPT

  # https://docs.astral.sh/uv/getting-started/installation/
  curl --fail --show-error --location https://astral.sh/uv/install.sh | sh

  # https://github.com/denoland/deno/issues/25931#issuecomment-2406073767
  curl --fail --show-error --location https://deno.land/install.sh | sh -s -- --yes
  # denoはシェルの設定の最終行に改行を追加しないので自前で追加する。
  echo | tee -a ~/.profile ~/.bashrc ~/.zshrc
SETUP_USER_DEVELOPER_LOCAL_ENVIRONMENT
