# SPDX-License-Identifier: CC0-1.0

from collections.abc import Mapping

import bpy
from bpy.types import Bone, Image, Material, Mesh, Object


def register() -> None:
    pass


def unregister() -> None:
    pass


class Vrm1ExportUserExtension:
    def pre_save_hook(
        self,
        json_chunk: dict[str, object],
        bin_chunk: bytearray,
        armature: Object,
        node_index_to_object: Mapping[int, Object],
        node_index_to_bone: Mapping[int, Bone],
        image_index_to_image: Mapping[int, Image],
        material_index_to_material: Mapping[int, Material],
        mesh_index_to_mesh: Mapping[int, Mesh],
    ) -> None:
        bpy.ops.mesh.primitive_cube_add(location=(1, 0, 0))
