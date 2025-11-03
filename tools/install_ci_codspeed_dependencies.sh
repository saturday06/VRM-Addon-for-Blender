#!/bin/sh

set -eux

export CMAKE_PREFIX_PATH=/opt/vrm

repository_root_path=$(
  cd "$(dirname "$0")/.."
  pwd
)
python_site_packages_path="${CMAKE_PREFIX_PATH}/lib/python3.12/site-packages"

mkdir -p "$python_site_packages_path"

mkdir -p /root/oneTBB/src
cd /root/oneTBB/src
# https://projects.blender.org/blender/lib-linux_x64/src/tag/v4.5.4/tbb/include/oneapi/tbb/version.h#L29-L36
curl --fail --show-error --location --retry 5 --retry-all-errors --output ../oneTBB.tar.gz \
  "https://github.com/uxlfoundation/oneTBB/archive/refs/tags/v2021.13.0.tar.gz"
tar zxf ../oneTBB.tar.gz --strip-components=1
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$CMAKE_PREFIX_PATH" -DTBB_TEST=OFF
cmake --build build --target install
ldconfig

mkdir -p /root/OpenImageIO/src
cd /root/OpenImageIO/src
# https://projects.blender.org/blender/lib-linux_x64/src/tag/v4.5.4/openimageio/include/OpenImageIO/oiioversion.h#L45-L49
curl --fail --show-error --location --retry 5 --retry-all-errors --output ../OpenImageIO.tar.gz \
  "https://github.com/AcademySoftwareFoundation/OpenImageIO/releases/download/v3.0.6.1/OpenImageIO-3.0.6.1.tar.gz"
tar zxf ../OpenImageIO.tar.gz --strip-components=1
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$CMAKE_PREFIX_PATH" -DOpenImageIO_BUILD_MISSING_DEPS=all -DOpenImageIO_BUILD_TESTS=OFF -DOpenImageIO_BUILD_TOOLS=OFF
cmake --build build --target install
ldconfig

mkdir -p /root/blender/blender
cd /root/blender/blender
curl --fail --show-error --location --output ../../blender.tar.xz \
  "https://download.blender.org/source/blender-4.5.4.tar.xz"
test "$(md5sum ../../blender.tar.xz)" = "885c50f870e606a2ede06c43be7e4a6a  ../../blender.tar.xz"
tar Jxf ../../blender.tar.xz --strip-components=1
./build_files/build_environment/install_linux_packages.py
make NPROCS=1 "BUILD_CMAKE_ARGS=-DPYTHON_VERSION=3.12 -DWITH_VULKAN_BACKEND=OFF" bpy
ldconfig

cp -r ../build_linux_bpy/bin/* "$python_site_packages_path"

export PYTHONPATH="${repository_root_path}/src:${python_site_packages_path}"
python3 -c 'import bpy; assert(bpy.app.version == (4, 5, 4))'
tar czf "${repository_root_path}/benchmark-dependencies.tar.gz" -C /opt vrm
