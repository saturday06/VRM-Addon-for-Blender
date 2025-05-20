# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender/src/tag/v4.3.0/scripts/addons_core/io_scene_gltf2/blender/exp/material/encode_image.py

from typing import Optional

from bpy.types import Image

class ExportImage:
    @staticmethod
    def from_blender_image(image: Image) -> ExportImage: ...
    def encode(
        self, mime_type: Optional[str], export_settings: dict[str, object]
    ) -> tuple[bytes, bool]: ...
