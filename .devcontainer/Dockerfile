FROM buildpack-deps:noble-curl

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# https://discourse.ubuntu.com/t/spec-apt-deb822-sources-by-default/29333#rationale-2
RUN sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources

# https://www.jetbrains.com/help/idea/prerequisites-for-dev-containers.html#remote_container
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get build-dep --yes --no-install-recommends \
        blender \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        alembic=* \
        bison=* \
        blender=* \
        build-essential=* \
        ca-certificates=* \
        cmake=* \
        curl=* \
        file=* \
        git=* \
        golang-go=* \
        less=* \
        libboost-dev=* \
        libbz2-dev=* \
        libdbus-1-dev=* \
        libdecor-0-dev=* \
        libegl-dev=* \
        libembree-dev=* \
        libepoxy-dev=* \
        libffi-dev=* \
        libfreetype6=* \
        libgl-dev=* \
        libjpeg-dev=* \
        liblzma-dev=* \
        libnanovdb-dev=* \
        libncurses-dev=* \
        libopenimageio-dev=* \
        libopenvdb-dev=* \
        libopenxr-dev=* \
        libreadline-dev=* \
        libsm6=* \
        libsqlite3-dev=* \
        libssl-dev=* \
        libwayland-dev=* \
        libx11-dev=* \
        libxcursor-dev=* \
        libxext6=* \
        libxi-dev=* \
        libxinerama-dev=* \
        libxkbcommon-dev=* \
        libxml2-dev=* \
        libxmlsec1-dev=* \
        libxrandr-dev=* \
        libxrender1=* \
        libxtst6=* \
        libxxf86vm-dev=* \
        libzstd-dev=* \
        locales=* \
        moreutils=* \
        ninja-build=* \
        nkf=* \
        opencollada-dev=* \
        openssh-client=* \
        patch=* \
        patchelf=* \
        procps=* \
        python3-dulwich=* \
        python3-numpy=* \
        python3-tqdm=* \
        python3-typing-extensions=* \
        ruby-rmagick=* \
        ruby=* \
        shellcheck=* \
        shfmt=* \
        subversion=* \
        sudo=* \
        tk-dev=* \
        unzip=* \
        wayland-protocols=* \
        xz-utils=* \
        yasm=* \
        zlib1g-dev=* \
        zopfli=* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# https://askubuntu.com/a/227513
RUN locale-gen en_US.UTF-8

WORKDIR /root/src

RUN if [ "$(uname -m)" = "aarch64" ]; then \
        mkdir -p sse2neon \
        && pushd sse2neon \
        && curl --fail --show-error --location https://github.com/DLTcollab/sse2neon/archive/refs/tags/v1.7.0.tar.gz \
            | tar zxf - --strip-components=1 \
        && make \
        && make check \
        && cp sse2neon.h /usr/local/include/ \
        && popd \
        && rm -fr sse2neon \
    ; fi

# poetryを経由して開発に利用するPythonを/usr/localにビルドしてインストールする。
# Python3.10系を使いたいがUbuntu 24.04のパッケージには存在しないので、自前でビルドする必要がある。
RUN mkdir -p python \
    && pushd python \
    && curl --fail --show-error --location https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tar.xz \
        | tar Jxf - --strip-components=1 \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -fr python \
    && ln -s /usr/local/bin/python3 /usr/local/bin/python

RUN /usr/local/bin/pip3 install numpy requests zstandard

# Linux用のbpyはx86_64版だけしかpypiに上がっていないため、それ以外の場合は自前でビルドしてシステムにインストールする。
# https://developer.blender.org/docs/handbook/building_blender/python_module/
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
        mkdir -p blender/blender \
        && pushd blender/blender \
        && curl --fail --show-error --location https://download.blender.org/source/blender-3.6.11.tar.xz \
            | tar Jxf - --strip-components=1 \
        && ./build_files/build_environment/install_linux_packages.py \
        && make NPROCS=1 bpy \
        && pushd ../build_linux_bpy \
        && make install \
        && cp -r bin/bpy /usr/local/lib/python3.10/site-packages/ \
        && popd \
        && popd \
        && rm -fr blender \
        && python3 -c 'import bpy; assert(bpy.app.version == (3, 6, 11))' \
    ; fi

RUN useradd --create-home --user-group --shell /bin/bash developer \
    && echo "developer ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/developer
USER developer
WORKDIR /home/developer

# "postCreateCommand" や "postStartCommand" でも使える環境変数を設定する。
# できれば "remoteEnv" で設定したいが、現在のJetBrains製品だと反映されないのでここで設定
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
ENV BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS=yes
ENV PATH=/home/developer/.local/bin:$PATH

# JetBrains製品は自動で `~/.cache` フォルダを作成するが、それだとフォルダの権限がroot:rootになる。
# poetryなどがエラーになるため、あらかじめ作っておく。
RUN mkdir -p .cache

RUN curl --fail --show-error --location https://install.python-poetry.org \
        | /usr/local/bin/python3 -

COPY --chown=developer:developer --chmod=700 install_hugo.sh .
RUN ./install_hugo.sh

COPY --chown=developer:developer --chmod=700 install_hadolint.sh .
RUN ./install_hadolint.sh
