# pypiパッケージの "bpy 3.6.0" がamd64にしか対応していないので、--platform=linux/amd64の決め打ちが必要
# https://pypi.org/project/bpy/3.6.0/
# hadolint ignore=DL3029
FROM --platform=linux/amd64 mcr.microsoft.com/devcontainers/python:3.10-bookworm
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    libgl1=* \
    libsm6=* \
    libxi6=* \
    libxkbcommon0=* \
    shellcheck=* \
    shfmt=* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER vscode

ENV PATH="/home/vscode/.local/bin:$PATH"
ENV BLENDER_VRM_TEST_BLENDER_PATH=/home/vscode/.local/blender/blender
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes

RUN curl --fail --show-error --location https://install.python-poetry.org \
    | python -

RUN mkdir -p ~/.local/blender
RUN curl --fail --show-error --location https://mirrors.ocf.berkeley.edu/blender/release/Blender2.93/blender-2.93.18-linux-x64.tar.xz \
    | tar -C ~/.local/blender -Jxf - --strip-components 1
