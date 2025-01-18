# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# https://docs.docker.com/build/building/best-practices/#sort-multi-line-arguments
# https://github.com/cli/cli/blob/v2.65.0/docs/install_linux.md#debian-ubuntu-linux-raspberry-pi-os-apt
RUN curl --fail --show-error --location --output /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        advancecomp=* \
        blender=* \
        curl=* \
        file=* \
        gh=* \
        git=* \
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
    && if [ "$(uname -m)" != "x86_64" ]; then \
        apt-get install -y --no-install-recommends \
            bison=* \
            cmake=* \
            g++=* \
            gcc=* \
            libboost-dev=* \
            libbz2-dev=* \
            libdbus-1-dev=* \
            libdecor-0-dev=* \
            libegl-dev=* \
            libembree-dev=* \
            libepoxy-dev=* \
            libffi-dev=* \
            libfftw3-dev=* \
            libfreetype6=* \
            libgl-dev=* \
            libglfw3-dev=* \
            libjpeg62-turbo-dev=* \
            libncurses-dev=* \
            libopenimageio-dev=* \
            libopenvdb-dev=* \
            libopenxr-dev=* \
            libpugixml-dev=* \
            libreadline-dev=* \
            libsqlite3-dev=* \
            libssl-dev=* \
            libtbb-dev=* \
            libwayland-dev=* \
            libx11-dev=* \
            libxcursor-dev=* \
            libxext6=* \
            libxi-dev=* \
            libxinerama-dev=* \
            libxkbcommon-dev=* \
            libxml2-dev=* \
            libxrandr-dev=* \
            libxtst-dev=* \
            libxxf86vm-dev=* \
            libzstd-dev=* \
            make=* \
            ninja-build=* \
            opencollada-dev=* \
            patchelf=* \
            subversion=* \
            tk-dev=* \
            wayland-protocols=* \
            yasm=* \
            zlib1g-dev=* \
    ; fi \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/src

# Linux用のbpyはx86_64版だけしかpypiに上がっていないため、それ以外の場合は自前でビルドしてシステムにインストールする。
# https://developer.blender.org/docs/handbook/building_blender/python_module/
RUN if [ "$(uname -m)" != "x86_64" ]; then \
        for path in /usr/local/lib /usr/local/lib64; do \
            mkdir -p "$path" \
            && echo "$path" >> /etc/ld.so.conf.d/vrm.conf \
        ; done \
        && ldconfig \
    ; fi

RUN if [ "$(uname -m)" = "aarch64" ]; then \
        curl --fail --show-error --location --output sse2neon.tar.gz https://github.com/DLTcollab/sse2neon/archive/refs/tags/v1.7.0.tar.gz \
        && test "$(md5sum sse2neon.tar.gz)" = "09e0a5ac47f852862c5c0e754462bc81  sse2neon.tar.gz" \
        && mkdir -p sse2neon \
        && pushd sse2neon \
        && tar zxf ../sse2neon.tar.gz --strip-components=1 \
        && make \
        && make check \
        && cp sse2neon.h /usr/local/include/ \
        && popd \
        && rm -fr sse2neon \
    ; fi

# ceresのビルド中にビルドが失敗することがある。失敗した場合はNPROCS=1を付与することで解決した。
# 発生していたエラーは次のとおり:
# [ 66%] Building C object source/blender/editors/animation/CMakeFiles/bf_editor_animation.dir/anim_channels_edit.c.o
# c++: fatal error: Killed signal terminated program cc1plus
# compilation terminated.
# make[3]: *** [extern/ceres/CMakeFiles/extern_ceres.dir/build.make:1952: extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o] Error 1
# make[3]: *** Deleting file 'extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o'
# 一般的には `make bpy || make NPROCS=1 bpy` という対応をするが、Parallels Desktop上のUbuntu Arm64 22.04だと
# GUI全体を巻き込んでクラッシュしたのでNPROCS=1で決め打ちする。
RUN if [ "$(uname -m)" != "x86_64" ]; then \
        curl --fail --show-error --location --output blender.tar.xz https://download.blender.org/source/blender-3.6.16.tar.xz \
        && test "$(md5sum blender.tar.xz)" = "72e043d16ea5dd3e7d9ce6a00c623919  blender.tar.xz" \
        && mkdir -p blender/blender \
        && pushd blender/blender \
        && tar Jxf ../../blender.tar.xz --strip-components=1 \
        && ./build_files/build_environment/install_linux_packages.py \
        && make NPROCS=1 bpy \
        && pushd ../build_linux_bpy \
        && make install \
        && cp -r bin/bpy /usr/local/lib/python3.10/site-packages/ \
        && popd \
        && popd \
        && rm -fr blender \
        && python3 -c 'import bpy; assert(bpy.app.version == (3, 6, 16))' \
    ; fi

RUN useradd --create-home --user-group --shell /bin/bash developer \
    && echo "developer ALL=(root) NOPASSWD:ALL" | tee /etc/sudoers.d/developer
USER developer
WORKDIR /home/developer

# "postCreateCommand" や "postStartCommand" でも使える環境変数を設定する。
# できれば "remoteEnv" で設定したいが、現在のJetBrains製品だと反映されないのでここで設定
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
ENV BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS=yes
ENV PATH=/home/developer/.cargo/bin:/home/developer/.local/bin:$PATH
ENV UV_LINK_MODE=copy

# JetBrains製品は自動で `~/.cache` フォルダを作成するが、それだとフォルダの権限がroot:rootになる。
# poetryなどがエラーになるため、あらかじめ作っておく。
RUN mkdir -p .cache

RUN curl --fail --show-error --location https://astral.sh/uv/install.sh | sh
RUN curl --fail --show-error --location https://fnm.vercel.app/install | bash
