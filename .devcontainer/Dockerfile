FROM buildpack-deps:mantic-curl

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV PATH="/opt/local/poetry/bin:$PATH"
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
        shellcheck=* \
        shfmt=* \
        sudo=* \
        tk-dev=* \
        xz-utils=* \
        zlib1g-dev=* \
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

RUN mkdir -p /usr/local/bin \
    && case "$(uname -m)" in \
        "x86_64") \
            curl --fail --show-error --location -o /usr/local/bin/hadolint \
                https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 \
            && chmod 755 /usr/local/bin/hadolint \
            ;; \
        "aarch64") \
            curl --fail --show-error --location -o /usr/local/bin/hadolint \
                https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-arm64 \
            && chmod 755 /usr/local/bin/hadolint \
            ;; \
        esac

RUN curl --fail --show-error --location https://install.python-poetry.org \
    | POETRY_HOME=/opt/local/poetry python3 -

RUN useradd --create-home --user-group --shell /bin/bash developer
USER developer
# JetBrainsのIDEは自動で `~/.cache` フォルダを作成するが、それだとフォルダの権限がroot:rootになる。
# poetryなどがエラーになるため、あらかじめ作っておく。
RUN mkdir -p ~/.cache
