# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py

from typing import overload

from bpy.types import Material
from io_scene_gltf2.io.com import gltf2_io

# In Blender versions before 3.2, there are 2 arguments
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
@overload
def gather_material(
    blender_material: Material,
    export_settings: dict[str, object],
) -> gltf2_io.Material | None: ...

# In Blender versions 3.2 and later, there are 3 arguments
# https://projects.blender.org/blender/blender-addons/src/tag/v3.2.0/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L31
@overload
def gather_material(
    blender_material: Material,
    active_uvmap_index: object,
    export_settings: dict[str, object],
) -> gltf2_io.Material | None: ...
