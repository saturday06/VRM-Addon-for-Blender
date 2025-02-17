# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
FROM rockylinux:9

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN dnf update -y \
    && dnf install-n -y dnf-plugins-core \
    && dnf config-manager --set-enabled crb \
    && dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo \
    && dnf install-n -y epel-release \
    && dnf update -y \
    && dnf install-n -y --setopt=install_weak_deps=False --allowerasing \
        ImageMagick \
        ShellCheck \
        advancecomp \
        blender \
        curl \
        file \
        gh \
        git \
        git-lfs \
        less \
        libSM \
        libXi \
        libxkbcommon \
        moreutils \
        nkf \
        openssh-clients \
        patchutils \
        python3-dulwich \
        python3-numpy \
        python3-tqdm \
        python3-typing-extensions \
        ruby \
        rubygems \
        sudo \
        unzip \
        xz \
        zopfli \
    && if [ "$(uname -m)" != "x86_64" ]; then \
            dnf install-n -y --setopt=install_weak_deps=False --allowerasing \
                OpenImageIO-devel \
                automake \
                autoconf \
                bison \
                boost-devel \
                bzip2-devel \
                cmake \
                dbus-devel \
                fftw-devel \
                freetype \
                gcc-c++ \
                gcc \
                glfw-devel \
                libSM \
                libX11-devel \
                libXcursor-devel \
                libXext \
                libXi-devel \
                libXinerama-devel \
                libXrandr-devel \
                libXtst-devel \
                libXxf86vm-devel \
                libdecor-devel \
                libepoxy-devel \
                libffi-devel \
                libjpeg-turbo-devel \
                libtool \
                libxkbcommon-devel \
                libxml2-devel \
                libzstd-devel \
                make \
                mesa-libEGL-devel \
                mesa-libGL-devel \
                ncurses-devel \
                ninja-build \
                openCOLLADA-devel \
                openssl-devel \
                openvdb-devel \
                openxr-devel \
                patchelf \
                pugixml-devel \
                readline-devel \
                sqlite-devel \
                subversion \
                tbb-devel \
                tk-devel \
                wayland-devel \
                wayland-protocols-devel \
                yasm \
                zlib-devel \
        ; fi \
    && dnf clean all

WORKDIR /root/src

# bpyを使いたいがLinux用のbpyはx86_64版だけしかpypiに上がっていないため、それ以外の場合は自前でビルドしてシステムにインストールする。
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
RUN if [ "$(uname -m)" != "x86_64" ]; then \
        curl --fail --show-error --location --output Python.tar.xz https://www.python.org/ftp/python/3.10.15/Python-3.10.15.tar.xz \
        && test "$(md5sum Python.tar.xz)" = "8b1faa1b193e4e90c0f17eb2decd89b5  Python.tar.xz" \
        && mkdir -p python \
        && pushd python \
        && tar Jxf ../Python.tar.xz --strip-components=1 \
        && ./configure \
        && make \
        && make install \
        && popd \
        && rm -fr python \
        && ln -s /usr/local/bin/python3 /usr/local/bin/python \
        && /usr/local/bin/pip3 install --no-cache-dir "numpy==1.23.*" "requests==2.27.*" "zstandard==0.16.*" \
    ; fi
RUN if [ "$(uname -m)" != "x86_64" ]; then \
        curl --fail --show-error --location --output embree.tar.gz https://github.com/RenderKit/embree/archive/refs/tags/v4.3.3.tar.gz \
        && test "$(md5sum embree.tar.gz)" = "170a7f8042fa89930f464cda0a0a63fc  embree.tar.gz" \
        && mkdir -p embree \
        && pushd embree \
        && tar zxf ../embree.tar.gz --strip-components=1 \
        && cmake . \
        && make \
        && make install \
        && popd \
        && rm -fr embree \
    ; fi
RUN if [ "$(uname -m)" != "x86_64" ]; then \
        curl --fail --show-error --location --output OpenSubdiv.tar.gz https://github.com/PixarAnimationStudios/OpenSubdiv/archive/refs/tags/v3_6_0.tar.gz \
        && test "$(md5sum OpenSubdiv.tar.gz)" = "cd03aaf8890bc0b8550eef62029cabe7  OpenSubdiv.tar.gz" \
        && mkdir -p OpenSubdiv \
        && pushd OpenSubdiv \
        && tar zxf ../OpenSubdiv.tar.gz --strip-components=1 \
        && cmake . \
        && make \
        && make install \
        && popd \
        && rm -fr OpenSubdiv \
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
        && dnf update -y \
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
    && usermod --append --groups wheel developer
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
