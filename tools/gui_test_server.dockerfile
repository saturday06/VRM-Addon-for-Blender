FROM debian:bookworm
ARG CI
ENV CI=$CI

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

RUN apt-get update -qq \
    && apt-get install --yes --no-install-recommends \
        "blender=*" \
        "curl=*" \
        "dbus=*" \
        "lxterminal=*" \
        "fvwm=*" \
        "less=*" \
        "mesa-utils=*" \
        "netcat-openbsd=*" \
        "openjdk-17-jre=*" \
        "procps=*" \
        "python3-numpy=*" \
        "recordmydesktop=*" \
        "x11-xserver-utils=*" \
        "x11vnc=*" \
        "xvfb=*" \
        "xz-utils=*" \
    && (if [ "$(uname -m)" = "aarch64" ]; then \
            apt-get install --yes --no-install-recommends \
                "libjxgrabkey-jni=*" \
                "libopencv4.5-jni=*" \
        ; fi) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --user-group --shell /bin/bash developer
USER developer
WORKDIR /home/developer

RUN curl -LSf --retry 5 https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5-lux.jar -o sikulixide.jar \
    && test "$(sha256sum < sikulixide.jar)" = "5e6948710561b1ca8ed29f09c2066a6176c610da053975b1d265d92747f12da0  -"

RUN mkdir noVNC \
    && curl -LSf --retry 5 https://github.com/novnc/noVNC/archive/cdfb33665195eb9a73fb00feb6ebaccd1068cd50.tar.gz | tar -C noVNC --strip-component=1 -zxf -

# https://github.com/novnc/noVNC/blob/cdfb33665195eb9a73fb00feb6ebaccd1068cd50/utils/novnc_proxy#L165
RUN mkdir noVNC/utils/websockify \
    && curl -LSf --retry 5 https://github.com/novnc/websockify/archive/33910d758d2c495dd1d380729c31bacbf8229ed0.tar.gz | tar -C noVNC/utils/websockify --strip-component=1 -zxf -

COPY tools/gui_test_server_entrypoint.sh /home/developer/
RUN mkdir -p /home/developer/var/log /home/developer/var/tmp /home/developer/tests /home/developer/src/io_scene_vrm
ENTRYPOINT ["/bin/sh", "-c", "dbus-run-session /home/developer/gui_test_server_entrypoint.sh 2>&1 | tee var/log/entrypoint.log"]

HEALTHCHECK CMD nc -z 127.0.0.1 5900 && curl --fail http://127.0.0.1:6000
