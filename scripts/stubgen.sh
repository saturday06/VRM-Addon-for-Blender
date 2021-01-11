#!/bin/sh

set -eux

stubgen \
  -p blf \
  -p bmesh \
  -p bpy_extras \
  -p gpu \
  -p gpu_extras \
  -p mathutils \
  -o "$(dirname "$0")/../stubs"
