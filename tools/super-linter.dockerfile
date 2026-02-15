# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
#
# HEALTHCHECK is not required since it does not operate as a server
# checkov:skip=CKV_DOCKER_2: "Ensure that HEALTHCHECK instructions have been added to container images"
#
# Do not create a new user as it runs with the super-linter user
# checkov:skip=CKV_DOCKER_3: "Ensure that a user for the container has been created"

FROM ghcr.io/super-linter/super-linter:v8.5.0@sha256:6831c0a801d353b510e4e468a3209a8a48bf0102e193d5c7e94e57667fdf64eb

# https://github.com/super-linter/super-linter/blob/v7.3.0/README.md?plain=1#L297
ENV LOG_LEVEL=WARN

# https://github.com/super-linter/super-linter/blob/v7.3.0/README.md?plain=1#L690
ENV RUN_LOCAL=true

# Exclude CHANGELOG.md as it is an automatically generated file by release-please
ENV FILTER_REGEX_EXCLUDE="^/tmp/lint/CHANGELOG\.md$"

ENV LINTER_RULES_PATH=/
ENV DEFAULT_BRANCH=main
ENV SAVE_SUPER_LINTER_SUMMARY=true

ENV GITHUB_ACTIONS_CONFIG_FILE=.github/actionlint.yaml
ENV MARKDOWN_CONFIG_FILE=.markdownlint.yaml

ENV VALIDATE_BIOME_FORMAT=false
ENV VALIDATE_BIOME_LINT=false
ENV VALIDATE_CSS=false
ENV VALIDATE_GIT_COMMITLINT=false
ENV VALIDATE_JSCPD=false
ENV VALIDATE_JSON=false
ENV VALIDATE_PYTHON_BLACK=false
ENV VALIDATE_PYTHON_ISORT=false
ENV VALIDATE_PYTHON_MYPY=false
ENV VALIDATE_PYTHON_PYLINT=false
ENV VALIDATE_PYTHON_RUFF=false
ENV VALIDATE_PYTHON_RUFF_FORMAT=false
ENV VALIDATE_TYPESCRIPT_ES=false
