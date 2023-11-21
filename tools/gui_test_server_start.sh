#!/bin/bash

set -eux -o pipefail

cd "$(dirname "$0")/.."

if ! command -v timeout; then
  timeout() (
    seconds=$1
    shift
    "$@" &
    wait_pid=$!

    for _ in $(seq "$seconds"); do
      if ! kill -0 "$wait_pid"; then
        exit 0
      fi
      sleep 1
    done

    kill "$wait_pid"
    exit 124
  )
fi

mkdir -p var/log var/tmp
docker_hash_path=var/repository_root_path_hash.txt
if command -v sha256sum; then
  echo "$PWD" | sha256sum - | awk '{print $1}' >"$docker_hash_path"
elif command -v shasum; then
  echo "$PWD" | shasum -a 256 - | awk '{print $1}' >"$docker_hash_path"
else
  echo "No hash command"
  exit 1
fi
docker_hash=$(cat "$docker_hash_path")
tag_name="vrm_addon_for_blender_gui_test_$docker_hash"
container_name="vrm_addon_for_blender_gui_test_container_$docker_hash"
CI=$(
  set +u
  echo "$CI"
)

running_container=$(docker ps --quiet --filter "name=$container_name")
if [ -n "$running_container" ]; then
  timeout 60 sh -c "until nc -z 127.0.0.1 6080; do sleep 0.1; done"
  exit 0
fi

docker build \
  . \
  --file tools/gui_test_server.dockerfile \
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
  timeout 30 sh -c "until docker exec '$container_name' glxinfo > /dev/null; do sleep 0.5; done"
  docker cp tests/resources/gui/. "$container_name:/root/tests"
  docker cp src/io_scene_vrm/. "$container_name:/root/io_scene_vrm"
else
  docker run \
    --detach \
    --publish "$publish" \
    --volume "$PWD/tests/resources/gui:/root/tests" \
    --volume "$PWD/var:/root/var" \
    --volume "$PWD/src/io_scene_vrm:/root/io_scene_vrm" \
    --rm \
    --name "$container_name" \
    "$tag_name"
  timeout 30 sh -c "until curl --silent --show-error --fail http://127.0.0.1:6080/vnc.html -o var/vnc.html; do sleep 0.5; done"
fi
