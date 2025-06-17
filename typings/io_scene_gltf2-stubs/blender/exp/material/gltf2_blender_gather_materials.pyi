# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v3.6.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py

from typing import overload

from bpy.types import Material
from io_scene_gltf2.io.com import gltf2_io

# Blender 4.0未満では引数は3つ
# https://projects.blender.org/blender/blender-addons/src/tag/v3.6.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py#L38
@overload
def gather_material(
    blender_material: Material,
    active_uvmap_index: object,
    export_settings: dict[str, object],
) -> gltf2_io.Material | None: ...

# Blender 4.0以降では引数は2つ
# https://projects.blender.org/blender/blender-addons/src/tag/v4.0.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py#L37
@overload
def gather_material(
    blender_material: Material, export_settings: dict[str, object]
) -> tuple[gltf2_io.Material | None, dict[str, object]]: ...
