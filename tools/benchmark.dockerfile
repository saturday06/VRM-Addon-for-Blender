# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
#
# HEALTHCHECK is not required since it does not operate as a server
# checkov:skip=CKV_DOCKER_2: "Ensure that HEALTHCHECK instructions have been added to container images"
#
# Do not create a new user as it runs with the super-linter user
# checkov:skip=CKV_DOCKER_3: "Ensure that a user for the container has been created"

FROM ubuntu:24.04 AS base

# https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  DEBIAN_FRONTEND=noninteractive apt-get update -q

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  DEBIAN_FRONTEND=noninteractive apt-get install \
    ca-certificates \
    python3 \
    python3-numpy \
    python3-requests \
    python3-zstandard \
    --no-install-recommends --yes

FROM base AS builder

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  DEBIAN_FRONTEND=noninteractive apt-get install \
    build-essential \
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
    subversion \
    sudo \
    wayland-protocols \
    xz-utils \
    --no-install-recommends --yes

WORKDIR /root/oneTBB/src
RUN curl --fail --show-error --location --retry 5 --retry-all-errors --output ../oneTBB.tar.gz \
  "https://github.com/uxlfoundation/oneTBB/archive/refs/tags/v2021.13.0.tar.gz"
RUN tar zxf ../oneTBB.tar.gz --strip-components=1
RUN cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DTBB_TEST=OFF
RUN cmake --build build --target install
RUN ldconfig

WORKDIR /root/OpenImageIO/src
RUN curl --fail --show-error --location --retry 5 --retry-all-errors --output ../OpenImageIO.tar.gz \
  "https://github.com/AcademySoftwareFoundation/OpenImageIO/releases/download/v3.0.6.1/OpenImageIO-3.0.6.1.tar.gz"
RUN tar zxf ../OpenImageIO.tar.gz --strip-components=1
RUN cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DOpenImageIO_BUILD_MISSING_DEPS=all -DOpenImageIO_BUILD_TESTS=OFF -DOpenImageIO_BUILD_TOOLS=OFF
RUN cmake --build build --target install
RUN cp -ru dist/* /usr/local/
RUN ldconfig

WORKDIR /root/blender/blender
RUN curl --fail --show-error --location --output ../../blender.tar.xz \
  "https://download.blender.org/source/blender-4.5.3.tar.xz"
RUN test "$(md5sum ../../blender.tar.xz)" = "66b39c54701706b74a53941edfe159f9  ../../blender.tar.xz"
RUN tar Jxf ../../blender.tar.xz --strip-components=1
RUN ./build_files/build_environment/install_linux_packages.py
RUN make NPROCS=1 "BUILD_CMAKE_ARGS=-DPYTHON_VERSION=3.12 -DWITH_VULKAN_BACKEND=OFF" bpy
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages
RUN mkdir -p "$PYTHONPATH"
RUN cp -r ../build_linux_bpy/bin/* "$PYTHONPATH"
RUN python3 -c 'import bpy; assert(bpy.app.version == (4, 5, 3))'

FROM base
COPY --from=builder /usr/local /usr/local
RUN ldconfig
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  DEBIAN_FRONTEND=noninteractive apt-get install \
    libembree4-4 \
    libepoxy0 \
    libfftw3-double3 \
    libfftw3-long3 \
    libfftw3-quad3 \
    libfftw3-single3 \
    libfreetype6 \
    libjpeg8 \
    libopenexr-3-1-30 \
    libosdgpu3.5.0t64 \
    libpng16-16t64 \
    libpugixml1v5 \
    libtiff6 \
    libwebp7 \
    libwebpdemux2 \
    libx11-6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    python3-venv \
    --no-install-recommends --yes
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages
RUN python3 -c 'import bpy; assert(bpy.app.version == (4, 5, 3))'
