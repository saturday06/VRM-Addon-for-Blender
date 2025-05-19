#
#

FROM ghcr.io/super-linter/super-linter:v7.4.0

ENV RUN_LOCAL=true

ENV FILTER_REGEX_EXCLUDE="^/tmp/lint/CHANGELOG\.md$"

ENV LINTER_RULES_PATH=/
