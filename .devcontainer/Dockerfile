# pypiパッケージの "bpy 3.6.0" がamd64にしか対応していないので、--platform=linux/amd64の決め打ちが必要
# https://pypi.org/project/bpy/3.6.0/
# hadolint ignore=DL3029
FROM --platform=linux/amd64 ubuntu:22.04
SHELL ["/bin/bash", "-o", "pipefail", "-l", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:$PATH"
ENV BLENDER_VRM_TEST_BLENDER_PATH=/root/.local/blender/blender
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    ca-certificates=* \
    curl=* \
    git=* \
    libgl1=* \
    libgomp1=* \
    libsm6=* \
    libxfixes3=* \
    libxi6=* \
    libxkbcommon0=* \
    libxrender1=* \
    libxxf86vm1=* \
    locales=* \
    openssh-client=* \
    python3.10=* \
    python-is-python3=* \
    shellcheck=* \
    shfmt=* \
    xz-utils=* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8

RUN curl --fail --show-error --location https://install.python-poetry.org \
    | python -

RUN mkdir -p ~/.local/blender
RUN curl --fail --show-error --location https://mirrors.ocf.berkeley.edu/blender/release/Blender2.93/blender-2.93.18-linux-x64.tar.xz \
    | tar -C ~/.local/blender -Jxf - --strip-components 1
