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

if [ "$(set +u; echo \$CI)" = "true" ]; then
  run_local=false
else
  run_local=true
fi

docker build --tag "$super_linter_tag_name" --file tools/super-linter.dockerfile .
exec docker run -e "RUN_LOCAL=$run_local" -v "$PWD:/tmp/lint" "$super_linter_tag_name"
