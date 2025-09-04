# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence
from typing import TypeVar

from bpy.types import Region, RegionView3D
from mathutils import Vector

def region_2d_to_vector_3d(
    region: Region,
    rv3d: RegionView3D,
    coord: Sequence[float],
) -> Vector: ...
def region_2d_to_origin_3d(
    region: Region,
    rv3d: RegionView3D,
    coord: Sequence[float],
    clamp: float | None = None,
) -> Vector: ...
def region_2d_to_location_3d(
    region: Region,
    rv3d: RegionView3D,
    coord: Sequence[float],
    depth_location: Sequence[float],
) -> Vector: ...

__Default = TypeVar("__Default")

def location_3d_to_region_2d(
    region: Region,
    rv3d: RegionView3D,
    coord: Sequence[float],
    default: __Default | None = None,
) -> Vector | __Default: ...
