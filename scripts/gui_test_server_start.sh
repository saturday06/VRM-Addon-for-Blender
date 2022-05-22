#!/bin/sh

set -eux
shellcheck "$0"

cd "$(dirname "$0")/.."
mkdir -p logs tmp
echo "$PWD" | sha256sum - | awk '{print $1}' > tmp/repository_root_path_hash.txt
docker_hash=$(cat tmp/repository_root_path_hash.txt)
tag_name="vrm_addon_for_blender_gui_test_$docker_hash"
container_name="vrm_addon_for_blender_gui_test_container_$docker_hash"

running_container=$(docker ps --quiet --filter "name=$container_name")
if [ -n "$running_container" ]; then
  exit 0
fi

docker build \
  . \
  --file scripts/gui_test_server.dockerfile \
  --tag "$tag_name" \
  --build-arg "CI=$(set +u; echo "$CI")"

publish=127.0.0.1:6080:6080/tcp
if [ "$CI" = "true" ]; then
  docker run \
    --detach \
    --publish "$publish" \
    --rm \
    --name "$container_name" \
    "$tag_name"
  docker cp tests/resources/gui/blender/vrm_addon/. "$container_name:/root/tests"
  docker cp io_scene_vrm/. "$container_name:/root/io_scene_vrm"
else
  docker run \
    --detach \
    --publish "$publish" \
    --volume logs:/root/logs \
    --volume tests/resources/gui/blender/vrm_addon:tests \
    --volume io_scene_vrm:/root/io_scene_vrm \
    --rm \
    --name "$container_name" \
    "$tag_name"
fi
