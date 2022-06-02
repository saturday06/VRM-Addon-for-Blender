#!/bin/sh

set -eux

if ! command -v shellcheck && [ "$(uname -s)" = "Darwin" ] && [ -x /opt/homebrew/bin/shellcheck ]; then
  /opt/homebrew/bin/shellcheck "$0"
else
  shellcheck "$0"
fi

cd "$(dirname "$0")/.."
mkdir -p logs tmp
docker_hash_path=tmp/repository_root_path_hash.txt
if command -v sha256sum; then
  echo "$PWD" | sha256sum - | awk '{print $1}' > "$docker_hash_path"
elif command -v shasum; then
  echo "$PWD" | shasum -a 256 - | awk '{print $1}' > "$docker_hash_path"
else
  echo "No hash command"
  exit 1
fi
docker_hash=$(cat "$docker_hash_path")
tag_name="vrm_addon_for_blender_gui_test_$docker_hash"
container_name="vrm_addon_for_blender_gui_test_container_$docker_hash"
CI=$(set +u; echo "$CI")

running_container=$(docker ps --quiet --filter "name=$container_name")
if [ -n "$running_container" ]; then
  exit 0
fi

docker build \
  . \
  --file scripts/gui_test_server.dockerfile \
  --tag "$tag_name" \
  --build-arg "CI=$CI"

publish=127.0.0.1:6080:6080/tcp
if [ "$CI" = "true" ]; then
  docker run \
    --detach \
    --publish "$publish" \
    --rm \
    --name "$container_name" \
    "$tag_name"
  docker cp tests/resources/gui/. "$container_name:/root/tests"
  docker cp io_scene_vrm/. "$container_name:/root/io_scene_vrm"
else
  docker run \
    --detach \
    --publish "$publish" \
    --volume "$PWD/logs:/root/logs" \
    --volume "$PWD/tests/resources/gui:/root/tests" \
    --volume "$PWD/io_scene_vrm:/root/io_scene_vrm" \
    --rm \
    --name "$container_name" \
    "$tag_name"
fi
