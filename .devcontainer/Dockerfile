# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
FROM mcr.microsoft.com/devcontainers/python:3.10-bookworm

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY debian.sources.patch /root/
RUN patch /etc/apt/sources.list.d/debian.sources /root/debian.sources.patch

# https://docs.docker.com/build/building/best-practices/#sort-multi-line-arguments
# https://github.com/cli/cli/blob/v2.65.0/docs/install_linux.md#debian-ubuntu-linux-raspberry-pi-os-apt
RUN <<'INSTALL_PACKAGES'
  set -eu
  curl --fail --show-error --location --output /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  apt-get update
  apt-get install \
    advancecomp=* \
    blender=* \
    curl=* \
    diffutils=* \
    file=* \
    gh=* \
    git=* \
    git-lfs=* \
    imagemagick=* \
    less=* \
    libsm6=* \
    libxi6=* \
    libxkbcommon0=* \
    moreutils=* \
    nkf=* \
    patchutils=* \
    python3-dulwich=* \
    python3-numpy=* \
    python3-tqdm=* \
    python3-typing-extensions=* \
    ruby=* \
    shellcheck=* \
    sudo=* \
    unzip=* \
    xz-utils=* \
    zopfli=* \
    -y --no-install-recommends

  if [ "$(uname -m)" != "x86_64" ]; then
    apt-get install -y --no-install-recommends libembree-dev=*
    apt-get --no-install-recommends -y build-dep blender
  fi
  rm -rf /var/lib/apt/lists/*
INSTALL_PACKAGES

WORKDIR /root/src

# bpyを使いたいがLinux用のbpyはx86_64版だけしかpypiに上がっていないため、それ以外の場合は自前でビルドしてシステムにインストールする。
# https://developer.blender.org/docs/handbook/building_blender/python_module/

# Blenderをビルドする
# ceresのビルド中にビルドが失敗することがある。失敗した場合はNPROCS=1を付与することで解決した。
# 発生していたエラーは次のとおり:
# [ 66%] Building C object source/blender/editors/animation/CMakeFiles/bf_editor_animation.dir/anim_channels_edit.c.o
# c++: fatal error: Killed signal terminated program cc1plus
# compilation terminated.
# make[3]: *** [extern/ceres/CMakeFiles/extern_ceres.dir/build.make:1952: extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o] Error 1
# make[3]: *** Deleting file 'extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o'
# 一般的には `make bpy || make NPROCS=1 bpy` という対応をするが、Parallels Desktop上のUbuntu Arm64 22.04だと
# GUI全体を巻き込んでクラッシュしたのでNPROCS=1で決め打ちする。
RUN <<'INSTALL_BLENDER'
  set -eu
  test "$(uname -m)" = "x86_64" && exit 0
  pip install --no-cache-dir "numpy==1.23.*" "requests==2.27.*" "zstandard==0.16.*"
  curl --fail --show-error --location --output blender.tar.xz https://download.blender.org/source/blender-3.6.21.tar.xz
  test "$(md5sum blender.tar.xz)" = "c7de02ee9057a3379b927c6be15aecae  blender.tar.xz"
  mkdir -p blender/blender
  pushd blender/blender
  tar Jxf ../../blender.tar.xz --strip-components=1
  ./build_files/build_environment/install_linux_packages.py
  make NPROCS=1 bpy
  pushd ../build_linux_bpy
  make install
  cp -r bin/bpy /usr/local/lib/python3.10/site-packages/
  popd
  popd
  rm -fr blender
  python -c 'import bpy; assert(bpy.app.version == (3, 6, 21))'
INSTALL_BLENDER

RUN <<'SETUP_USER_DEVELOPER'
  set -eu
  useradd --create-home --user-group --shell /bin/bash developer
  echo "developer ALL=(root) NOPASSWD:ALL" | tee /etc/sudoers.d/developer
  mkdir -p /workspace
  chown developer:developer /workspace
SETUP_USER_DEVELOPER

USER developer
WORKDIR /home/developer

# "postCreateCommand" や "postStartCommand" でも使える環境変数を設定する。
# できれば "remoteEnv" で設定したいが、現在のJetBrains製品だと反映されないのでここで設定
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
ENV BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS=yes
ENV PATH=/home/developer/.deno/bin:/home/developer/.cargo/bin:/home/developer/.local/bin:$PATH
ENV UV_LINK_MODE=copy

# JetBrains製品は自動で `~/.cache` フォルダを作成するが、それだとフォルダの権限がroot:rootになる。
# poetryなどがエラーになるため、あらかじめ作っておく。
RUN mkdir -p .cache

RUN curl --fail --show-error --location https://astral.sh/uv/install.sh | sh
RUN curl --fail --show-error --location https://deno.land/install.sh | sh
