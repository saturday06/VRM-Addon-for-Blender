# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import tempfile
from pathlib import Path
from unittest import TestCase, main

import bpy

from io_scene_vrm.external import io_scene_gltf2_support


class TestIoSceneGltf2Support(TestCase):
    def test_image_to_image_bytes(self) -> None:
        context = bpy.context

        tga_path = Path(__file__).parent.parent / "resources" / "blend" / "tga_test.tga"
        image = context.blend_data.images.load(str(tga_path), check_existing=True)
        image_bytes, _ = io_scene_gltf2_support.image_to_image_bytes(
            image, io_scene_gltf2_support.create_export_settings()
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "image.png"
            temp_path.write_bytes(image_bytes)
            converted_image = context.blend_data.images.load(
                str(temp_path), check_existing=False
            )
            converted_image.update()

        self.assertEqual(image.size[:], converted_image.size[:])


if __name__ == "__main__":
    main()
