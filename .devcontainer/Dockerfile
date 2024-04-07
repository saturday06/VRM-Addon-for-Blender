FROM buildpack-deps:noble-curl

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV PATH="/usr/local/poetry/bin:$PATH"
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes
ENV BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS=yes

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        blender=* \
        build-essential=* \
        ca-certificates=* \
        curl=* \
        file=* \
        git=* \
        golang-go=* \
        less=* \
        libbz2-dev=* \
        libffi-dev=* \
        liblzma-dev=* \
        libncurses-dev=* \
        libreadline-dev=* \
        libsm6=* \
        libsqlite3-dev=* \
        libssl-dev=* \
        libxml2-dev=* \
        libxmlsec1-dev=* \
        locales=* \
        moreutils=* \
        nkf=* \
        openssh-client=* \
        python3-dulwich=* \
        python3-numpy=* \
        python3-tqdm=* \
        python3-typing-extensions=* \
        ruby=* \
        ruby-rmagick=* \
        shellcheck=* \
        shfmt=* \
        sudo=* \
        tk-dev=* \
        xz-utils=* \
        zlib1g-dev=* \
        zopfli=* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# https://askubuntu.com/a/227513
RUN locale-gen en_US.UTF-8

# cdを使うと警告が出るため、pushdを使うことで回避する
# https://github.com/hadolint/hadolint/issues/422
RUN mkdir -p PythonSource \
    && pushd PythonSource \
    && curl --fail --show-error --location https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tar.xz \
        | tar Jxf - --strip-components 1 \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -fr PythonSource

RUN curl --fail --show-error --location https://install.python-poetry.org \
    | POETRY_HOME=/usr/local/poetry /usr/local/bin/python3 -

RUN useradd --create-home --user-group --shell /bin/bash developer \
    && echo "developer ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/developer
USER developer
# JetBrainsのIDEは自動で `~/.cache` フォルダを作成するが、それだとフォルダの権限がroot:rootになる。
# poetryなどがエラーになるため、あらかじめ作っておく。
RUN mkdir -p ~/.cache

############################## Non x86_64 ##############################
# Linux用のbpyはx86_64版だけしかpypiに上がっていないため、それ以外の場合は自前でビルドしてシステムにインストールする。
# https://developer.blender.org/docs/handbook/building_blender/python_module/

# 開発用に中断・再開が容易になるように、冗長になるが処理ごとに `[ "$(uname -m)" = "x86_64" ] || ` をつける。
USER root
WORKDIR /root
RUN [ "$(uname -m)" = "x86_64" ] || sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
RUN [ "$(uname -m)" = "x86_64" ] || (apt-get update \
                                        && apt-get build-dep --yes --no-install-recommends blender \
                                        && apt-get install --yes --no-install-recommends \
                                            alembic=* \
                                            bison=* \
                                            libboost-dev=* \
                                            libembree-dev=* \
                                            libepoxy-dev=* \
                                            libjpeg-dev=* \
                                            libnanovdb-dev=* \
                                            libopenimageio-dev=* \
                                            libopenvdb-dev=* \
                                            libopenxr-dev=* \
                                            libzstd-dev=* \
                                            opencollada-dev=* \
                                            patchelf=* \
                                            yasm=* \
                                        && apt-get clean \
                                        && rm -rf /var/lib/apt/lists/*)
RUN [ "$(uname -m)" = "x86_64" ] || /usr/local/bin/pip3 install numpy requests zstandard

USER developer
WORKDIR /home/developer/src/sse2neon
RUN [ "$(uname -m)" = "x86_64" ] || curl --fail --show-error --location \
                                        https://github.com/DLTcollab/sse2neon/archive/refs/tags/v1.7.0.tar.gz \
                                        | tar zxf - --strip-components=1
RUN [ "$(uname -m)" = "x86_64" ] || make
RUN [ "$(uname -m)" = "x86_64" ] || make check

USER root
RUN [ "$(uname -m)" = "x86_64" ] || cp sse2neon.h /usr/local/include/

USER developer
WORKDIR /home/developer/src/blender/blender
RUN [ "$(uname -m)" = "x86_64" ] || curl --fail --show-error --location \
                                        https://download.blender.org/source/blender-3.6.9.tar.xz \
                                        | tar Jxf - --strip-components=1

USER root
RUN [ "$(uname -m)" = "x86_64" ] || ./build_files/build_environment/install_linux_packages.py

USER developer
# ceresのビルド中にビルドが失敗することがある。失敗した場合はNPROCS=1を付与することで解決した。
# 発生していたエラーは次のとおり:
# [ 66%] Building C object source/blender/editors/animation/CMakeFiles/bf_editor_animation.dir/anim_channels_edit.c.o
# c++: fatal error: Killed signal terminated program cc1plus
# compilation terminated.
# make[3]: *** [extern/ceres/CMakeFiles/extern_ceres.dir/build.make:1952: extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o] Error 1
# make[3]: *** Deleting file 'extern/ceres/CMakeFiles/extern_ceres.dir/internal/ceres/generated/schur_eliminator_2_2_3.cc.o'
# 一般的には `make bpy || make NPROCS=1 bpy` という対応をするが、Parallels Desktop上のUbuntu Arm64 22.04だと
# GUI全体を巻き込んでクラッシュしたのでNPROCS=1で決め打ちする。
RUN [ "$(uname -m)" = "x86_64" ] || make NPROCS=1 bpy

WORKDIR /home/developer/src/blender/build_linux_bpy
RUN [ "$(uname -m)" = "x86_64" ] || make install

USER root
RUN [ "$(uname -m)" = "x86_64" ] || cp -r bin/bpy /usr/local/lib/python3.10/site-packages/

USER developer
RUN [ "$(uname -m)" = "x86_64" ] || python3 -c 'import bpy; assert(bpy.app.version == (3, 6, 9))'
