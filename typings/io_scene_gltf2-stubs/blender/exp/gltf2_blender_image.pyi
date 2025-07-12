# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py

from typing import overload

from bpy.types import Image

class ExportImage:
    @staticmethod
    def from_blender_image(image: Image) -> ExportImage: ...

    # In Blender versions before 3.3, there is 1 argument and 1 return value
    # https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L107
    # In Blender versions 3.3 and later but before 3.5, there is 1 argument and 2 values
    # https://projects.blender.org/blender/blender-addons/src/tag/v3.3.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L128
    @overload
    def encode(self, mime_type: str | None) -> bytes | tuple[bytes, bool]: ...

    # In Blender versions 3.5 and later, there are 2 arguments and 2 return values
    # https://projects.blender.org/blender/blender-addons/src/tag/v3.5.0/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L128
    @overload
    def encode(
        self, mime_type: str | None, export_settings: dict[str, object]
    ) -> tuple[bytes, bool]: ...
