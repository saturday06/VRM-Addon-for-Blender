import tempfile
from pathlib import Path

import bpy

from io_scene_vrm.external import io_scene_gltf2_support


def test() -> None:
    tga_path = Path(__file__).parent / "resources" / "blend" / "tga_test.tga"
    image = bpy.data.images.load(str(tga_path), check_existing=True)
    image_bytes, _ = io_scene_gltf2_support.image_to_image_bytes(
        image, io_scene_gltf2_support.create_export_settings()
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "image.png"
        temp_path.write_bytes(image_bytes)

        converted_image = bpy.data.images.load(str(temp_path), check_existing=False)
        converted_image.update()

    assert image.size[:] == converted_image.size[:]


if __name__ == "__main__":
    test()
