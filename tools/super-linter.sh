#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

pwd_and_system="$(pwd):$(uname -a)"
case "$(uname -s)" in
"Linux")
  pwd_and_system_hash=$(echo "$pwd_and_system" | md5sum | cut -d" " -f 1)
  ;;
"Darwin")
  pwd_and_system_hash=$(echo "$pwd_and_system" | md5)
  ;;
*)
  exit 0
  ;;
esac
super_linter_tag_name="super-linter-local-${pwd_and_system_hash}"

docker build --platform=linux/amd64 --tag "$super_linter_tag_name" --file tools/super-linter.dockerfile .
exec docker run -v "$PWD:/tmp/lint" "$super_linter_tag_name"
