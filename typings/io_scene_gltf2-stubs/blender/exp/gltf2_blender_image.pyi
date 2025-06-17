# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py

from typing import overload

from bpy.types import Image

class ExportImage:
    @staticmethod
    def from_blender_image(image: Image) -> ExportImage: ...

    # Blender 3.3未満では引数は1つ、戻り値は1つ
    # https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L107
    # Blender 3.3以降かつ3.5未満では引数は1つ、戻り値は2つ
    # https://projects.blender.org/blender/blender-addons/src/tag/v3.3.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L128
    @overload
    def encode(self, mime_type: str | None) -> bytes | tuple[bytes, bool]: ...

    # Blender 3.5以降では引数は2つ、戻り値は2つ
    # https://projects.blender.org/blender/blender-addons/src/tag/v3.5.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L128
    @overload
    def encode(
        self, mime_type: str | None, export_settings: dict[str, object]
    ) -> tuple[bytes, bool]: ...
