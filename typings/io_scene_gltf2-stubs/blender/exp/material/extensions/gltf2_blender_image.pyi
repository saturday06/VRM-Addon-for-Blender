# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v3.6.0/io_scene_gltf2/blender/exp/material/extensions/gltf2_blender_image.py

from typing import Optional

from bpy.types import Image

class ExportImage:
    @staticmethod
    def from_blender_image(image: Image) -> ExportImage: ...
    def encode(
        self, mime_type: Optional[str], export_settings: dict[str, object]
    ) -> tuple[bytes, bool]: ...
