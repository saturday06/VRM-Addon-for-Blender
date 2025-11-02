#!/bin/sh

set -eux

export DEBIAN_FRONTEND=noninteractive
export CMAKE_PREFIX_PATH=/opt/vrm

repository_root_path=$(
  cd "$(dirname "$0")/.."
  pwd
)

apt-get update -q
apt-get install \
  build-essential \
  ca-certificates \
  cmake \
  cmake-curses-gui \
  cmake-gui patch \
  curl \
  git \
  git-lfs \
  libboost-dev \
  libdbus-1-dev \
  libdecor-0-dev \
  libegl-dev \
  libembree-dev \
  libepoxy-dev \
  libfftw3-dev \
  libfreetype-dev \
  libgl-dev \
  libgmp-dev \
  libopenexr-dev \
  libosd-dev \
  libpng-dev \
  libpugixml-dev \
  libpython3-dev \
  libshaderc-dev \
  libtbb-dev \
  libtiff-dev \
  libvulkan-dev \
  libwayland-dev \
  libx11-dev \
  libxcursor-dev \
  libxi-dev \
  libxinerama-dev \
  libxkbcommon-dev \
  libxrandr-dev \
  libxxf86vm-dev \
  libzstd-dev \
  ninja-build \
  pybind11-dev \
  python3 \
  python3-numpy \
  python3-venv \
  python3-requests \
  python3-zstandard \
  subversion \
  wayland-protocols \
  xz-utils \
  --no-install-recommends --yes

mkdir -p /root/oneTBB/src
cd /root/oneTBB/src
curl --fail --show-error --location --retry 5 --retry-all-errors --output ../oneTBB.tar.gz \
  "https://github.com/uxlfoundation/oneTBB/archive/refs/tags/v2021.13.0.tar.gz"
tar zxf ../oneTBB.tar.gz --strip-components=1
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/vrm -DTBB_TEST=OFF
cmake --build build --target install
ldconfig

mkdir -p /root/OpenImageIO/src
cd /root/OpenImageIO/src
curl --fail --show-error --location --retry 5 --retry-all-errors --output ../OpenImageIO.tar.gz \
  "https://github.com/AcademySoftwareFoundation/OpenImageIO/releases/download/v3.0.6.1/OpenImageIO-3.0.6.1.tar.gz"
tar zxf ../OpenImageIO.tar.gz --strip-components=1
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DOpenImageIO_BUILD_MISSING_DEPS=all -DOpenImageIO_BUILD_TESTS=OFF -DOpenImageIO_BUILD_TOOLS=OFF
cmake --build build --target install
cp -ru dist/* /opt/vrm/
ldconfig

mkdir -p /root/blender/blender
cd /root/blender/blender
curl --fail --show-error --location --output ../../blender.tar.xz \
  "https://download.blender.org/source/blender-4.5.3.tar.xz"
test "$(md5sum ../../blender.tar.xz)" = "66b39c54701706b74a53941edfe159f9  ../../blender.tar.xz"
tar Jxf ../../blender.tar.xz --strip-components=1
./build_files/build_environment/install_linux_packages.py
make NPROCS=1 "BUILD_CMAKE_ARGS=-DPYTHON_VERSION=3.12 -DWITH_VULKAN_BACKEND=OFF" bpy
ldconfig

site_packages_path=/opt/vrm/lib/python3.12/site-packages
mkdir -p "$site_packages_path"
cp -r ../build_linux_bpy/bin/* "$site_packages_path"

export PYTHONPATH="${repository_root_path}/src:${site_packages_path}"
python3 -c 'import bpy; assert(bpy.app.version == (4, 5, 3))'
tar czf "${repository_root_path}/benchmark-dependencies.tar.gz" -C /opt vrm

echo "PYTHONPATH=${PYTHONPATH}" >>"$GITHUB_ENV"
