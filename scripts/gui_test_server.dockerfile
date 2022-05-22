FROM ubuntu:jammy
ARG CI
ENV CI=$CI

WORKDIR /root
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0
ENV LIBGL_ALWAYS_INDIRECT=1
ENV LANG en_US.UTF-8

RUN apt-get update -qq \
    && apt-get dist-upgrade --yes \
    && apt-get install --yes --no-install-recommends locales \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 \
    && apt-get install --yes --no-install-recommends \
        curl \
        dbus \
        git \
        gnome-terminal \
        fvwm \
        less \
        libgl1-mesa-glx \
        locales \
        mesa-utils \
        openjdk-17-jdk \
        python3-numpy \
        recordmydesktop \
        shellcheck \
        x11vnc \
        xvfb \
        xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LSf https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5-lux.jar -o sikulixide.jar \
    && test "$(cat sikulixide.jar | sha256sum -)" = "5e6948710561b1ca8ed29f09c2066a6176c610da053975b1d265d92747f12da0  -"

RUN curl -LSf https://download.blender.org/release/Blender2.83/blender-2.83.20-linux-x64.tar.xz -o blender.tar.xz \
    && test "$(cat blender.tar.xz | sha256sum -)" = "2ae3f26f7f49f9352b70f505b8f363d0cb51b214b86661d94ee4e9c588c414f8  -" \
    && mkdir blender \
    && tar xf blender.tar.xz -C blender --strip-components 1 \
    && rm blender.tar.xz

RUN mkdir noVNC \
    && cd noVNC \
    && git init \
    && git remote add origin https://github.com/novnc/noVNC.git \
    && git fetch --depth 1 origin cdfb33665195eb9a73fb00feb6ebaccd1068cd50 \
    && git checkout FETCH_HEAD \
    && rm -fr .git

# https://github.com/novnc/noVNC/blob/cdfb33665195eb9a73fb00feb6ebaccd1068cd50/utils/novnc_proxy#L165
RUN mkdir noVNC/utils/websockify \
    && cd noVNC/utils/websockify \
    && git init \
    && git remote add origin https://github.com/novnc/websockify.git \
    && git fetch --depth 1 origin 4b194636e2af1e4dda2a7f6fb1b576e42c3b5ade \
    && git checkout FETCH_HEAD \
    && rm -fr .git

RUN curl -LSf https://github.com/saturday06/VRM_Addon_for_Blender/raw/release-archive/VRM_Addon_for_Blender-release.zip -o ../VRM_Addon_for_Blender-release.zip

COPY scripts/gui_test_server_entrypoint.sh /root/
RUN mkdir -p /root/logs /root/tests /root/io_scene_vrm
ENTRYPOINT dbus-run-session /root/gui_test_server_entrypoint.sh | tee logs/entrypoint.txt
