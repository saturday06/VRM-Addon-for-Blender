# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender/src/tag/v4.3.0/scripts/addons_core/io_scene_gltf2/blender/exp/material/materials.py

from bpy.types import Material
from io_scene_gltf2.io.com import gltf2_io

def gather_material(
    blender_material: Material, export_settings: dict[str, object]
) -> tuple[gltf2_io.Material | None, dict[str, object]]: ...
