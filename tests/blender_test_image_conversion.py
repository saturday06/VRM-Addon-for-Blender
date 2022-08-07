import tempfile
from os.path import dirname, join

import bpy

from io_scene_vrm.external import io_scene_gltf2_support


def test() -> None:
    tga_path = join(dirname(__file__), "resources", "blend", "tga_test.tga")
    image = bpy.data.images.load(tga_path, check_existing=True)
    image_bytes, _ = io_scene_gltf2_support.image_to_image_bytes(image)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = join(temp_dir, "image.png")
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        converted_image = bpy.data.images.load(temp_path, check_existing=False)
        converted_image.update()

    assert image.size[:] == converted_image.size[:]


if __name__ == "__main__":
    test()
