# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
#
# HEALTHCHECK is not required since it does not operate as a server
# checkov:skip=CKV_DOCKER_2: "Ensure that HEALTHCHECK instructions have been added to container images"
#
# Do not create a new user as it runs with the super-linter user
# checkov:skip=CKV_DOCKER_3: "Ensure that a user for the container has been created"

FROM ghcr.io/super-linter/super-linter:v9.0.0@sha256:7620fb6f07a1908b0642d9ddc4f49da7d9f2b9497bcafee4d3d151d1e5567c0b

# Workflow dependency lockfiles require zizmor 1.32.0 or later.
RUN if /venvs/zizmor/bin/python -c \
    'import importlib.metadata; import sys; from pip._vendor.packaging.version import Version; sys.exit(Version(importlib.metadata.version("zizmor")) >= Version("1.32.0"))'; then \
    /venvs/zizmor/bin/pip install --no-cache-dir zizmor==1.32.0; \
    fi

# https://github.com/super-linter/super-linter/blob/v7.3.0/README.md?plain=1#L297
ENV LOG_LEVEL=WARN

# https://github.com/super-linter/super-linter/blob/v7.3.0/README.md?plain=1#L690
ENV RUN_LOCAL=true

# Exclude CHANGELOG.md as it is an automatically generated file by release-please
ENV FILTER_REGEX_EXCLUDE="^/tmp/lint/CHANGELOG\.md$"

# https://github.com/super-linter/super-linter?tab=readme-ov-file#configure-linters
ENV LINTER_RULES_PATH=.

ENV DEFAULT_BRANCH=HEAD
ENV SAVE_SUPER_LINTER_SUMMARY=true

# Exclude installed dependencies and local caches from recursive Trivy scans.
ENV TRIVY_SKIP_DIRS="node_modules,.local,.venv,benchmarks/.venv"

ENV GITHUB_ACTIONS_CONFIG_FILE=.github/actionlint.yaml
ENV MARKDOWN_CONFIG_FILE=.markdownlint.yaml

ENV VALIDATE_BIOME_FORMAT=false
ENV VALIDATE_BIOME_LINT=false
ENV VALIDATE_CSS=false
ENV VALIDATE_GIT_COMMITLINT=false
ENV VALIDATE_JSCPD=false
ENV VALIDATE_JSON_PRETTIER=false
ENV VALIDATE_JSON=false
ENV VALIDATE_PYTHON_BLACK=false
ENV VALIDATE_PYTHON_ISORT=false
ENV VALIDATE_PYTHON_MYPY=false
ENV VALIDATE_PYTHON_PYLINT=false
ENV VALIDATE_PYTHON_RUFF_FORMAT=false
ENV VALIDATE_PYTHON_RUFF=false
ENV VALIDATE_SPELL_CODESPELL=false
ENV VALIDATE_TYPESCRIPT_ES=false
ENV VALIDATE_TYPESCRIPT_PRETTIER=false
ENV VALIDATE_VUE_PRETTIER=false
ENV VALIDATE_YAML_PRETTIER=false
