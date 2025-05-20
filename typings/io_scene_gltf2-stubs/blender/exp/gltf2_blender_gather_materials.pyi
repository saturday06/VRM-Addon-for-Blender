# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py

from typing import Optional, overload

from bpy.types import Material
from io_scene_gltf2.io.com import gltf2_io

# Blender 3.2未満では引数は2つ
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
@overload
def gather_material(
    blender_material: Material,
    export_settings: dict[str, object],
) -> Optional[gltf2_io.Material]: ...

# Blender 3.2以降では引数は3つ
# https://projects.blender.org/blender/blender-addons/src/tag/v3.2.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L31
@overload
def gather_material(
    blender_material: Material,
    active_uvmap_index: object,
    export_settings: dict[str, object],
) -> Optional[gltf2_io.Material]: ...
