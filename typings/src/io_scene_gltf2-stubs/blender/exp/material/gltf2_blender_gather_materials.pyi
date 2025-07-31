# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v3.6.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py

from typing import overload

from bpy.types import Material
from io_scene_gltf2.io.com import gltf2_io

# In Blender versions before 4.0, there are 3 arguments
# https://projects.blender.org/blender/blender-addons/src/tag/v3.6.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py#L38
@overload
def gather_material(
    blender_material: Material,
    active_uvmap_index: object,
    export_settings: dict[str, object],
) -> gltf2_io.Material | None: ...

# In Blender versions 4.0 and later, there are 2 arguments
# https://projects.blender.org/blender/blender-addons/src/tag/v4.0.0/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py#L37
@overload
def gather_material(
    blender_material: Material, export_settings: dict[str, object]
) -> tuple[gltf2_io.Material | None, dict[str, object]]: ...
