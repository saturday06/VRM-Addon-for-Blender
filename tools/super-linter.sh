#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

docker_tag="super-linter-$(
  find . -type f -name "*.py" -o -name "*.sh" | sort | xargs sha256sum | sha256sum | cut -d " " -f 1
)"

docker build -t "$docker_tag" -f .github/super-linter.Dockerfile .
docker run --rm -v "$(pwd):/tmp/lint" "$docker_tag"
