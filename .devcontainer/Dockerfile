FROM quay.io/centos/centos:stream9

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV PATH="/opt/local/poetry/bin:/opt/local/blender:$PATH"
ENV BLENDER_VRM_LOGGING_LEVEL_DEBUG=yes

# DL3041はいきなり導入は厳しいので運用がこなれてくるまではignoreする
# hadolint ignore=DL3041
RUN dnf install --assumeyes 'dnf-command(config-manager)' \
    && dnf config-manager --set-enabled crb \
    && dnf install --assumeyes epel-release \
    && dnf install --assumeyes \
        ShellCheck \
        git \
        sudo \
        xz \
    &&  if [ "$(uname -m)" == "aarch64" ]; then \
            dnf install --assumeyes blender; \
            echo 'export BLENDER_VRM_DEVCONTAINER_TEST_GENERATION_USING_SUBPROCESS="yes"' >> /etc/profile.d/50-blender-vrm.sh; \
            curl --fail --show-error --location https://github.com/mvdan/sh/releases/download/v3.8.0/shfmt_v3.8.0_linux_arm64 > /usr/local/bin/shfmt; \
        else \
            dnf install --assumeyes \
                libSM \
                libXi \
                libxkbcommon \
            ; \
            mkdir -p /opt/local/blender; \
            curl --fail --show-error --location https://mirrors.ocf.berkeley.edu/blender/release/Blender2.93/blender-2.93.18-linux-x64.tar.xz \
                | tar Jxf - -C /opt/local/blender --strip-components 1; \
            curl --fail --show-error --location https://github.com/mvdan/sh/releases/download/v3.8.0/shfmt_v3.8.0_linux_amd64 > /usr/local/bin/shfmt; \
        fi \
    && chmod 755 /usr/local/bin/shfmt \
    && dnf builddep --assumeyes python3 \
    && dnf clean all \
    && rm -rf /var/cache/yum

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
    | POETRY_HOME=/opt/local/poetry python3 -

RUN useradd --create-home --user-group blender-vrm --groups wheel \
    && echo "blender-vrm ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/blender-vrm
