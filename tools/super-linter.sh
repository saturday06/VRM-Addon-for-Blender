#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

# 別のフォルダや別のシステムで作業中のdockerイメージと重複しないように
# それらをまとめたハッシュ値をdockerのタグ名としてビルドをする
dir_and_system="$(uname -a):$(pwd)"
case "$(uname -s)" in
"Linux")
  dir_and_system_md5=$(echo "$dir_and_system" | md5sum | cut -d" " -f 1)
  ;;
"Darwin")
  dir_and_system_md5=$(echo "$dir_and_system" | md5)
  ;;
*)
  exit 0
  ;;
esac
super_linter_tag_name="super-linter-local-${dir_and_system_md5}"
docker build --tag "$super_linter_tag_name" --file tools/super-linter.dockerfile .
# CHANGELOG.mdはrelease-pleaseによる自動生成ファイル
docker run \
  -e LOG_LEVEL=INFO \
  -e RUN_LOCAL=true \
  -e LINTER_RULES_PATH=/ \
  -e FILTER_REGEX_EXCLUDE="^/CHANGELOG\.md$" \
  -e DEFAULT_BRANCH=main \
  -e SAVE_SUPER_LINTER_SUMMARY=true \
  -e MARKDOWN_CONFIG_FILE=.markdownlint.yaml \
  -e GITHUB_ACTIONS_CONFIG_FILE=.github/actionlint.yaml \
  -e VALIDATE_GO=false \
  -e VALIDATE_GO_MODULES=false \
  -e VALIDATE_HTML=false \
  -e VALIDATE_JAVASCRIPT_STANDARD=false \
  -e VALIDATE_JSCPD=false \
  -e VALIDATE_JSON=false \
  -e VALIDATE_PYTHON_BLACK=false \
  -e VALIDATE_PYTHON_ISORT=false \
  -e VALIDATE_PYTHON_MYPY=false \
  -e VALIDATE_PYTHON_PYINK=false \
  -e VALIDATE_PYTHON_PYLINT=false \
  -v "$PWD:/tmp/lint" \
  "$super_linter_tag_name"
