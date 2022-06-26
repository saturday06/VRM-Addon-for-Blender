"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

#
#
# Please don't import anything in global scope to detect script reloading and minimize initialization.
#
#

bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (2, 4, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import-Edit-Export VRM",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "doc_url": "https://vrm-addon-for-blender.info",
    "tracker_url": "https://github.com/saturday06/VRM_Addon_for_Blender/issues",
    "category": "Import-Export",
}


def register() -> None:
    import os

    import bpy

    if bpy.app.version < bl_info["blender"]:
        raise Exception(
            f"This add-on doesn't support Blender version less than {bl_info['blender']} "
            + f"but the current version is {bpy.app.version}"
        )

    # For users who have acquired the add-on from "Code" -> "Download ZIP" on GitHub.
    github_code_download_zip_path = os.path.join(
        os.path.dirname(__file__),
        ".github",
        "vrm_addon_for_blender_private",
        "_".join(map(str, bl_info["version"])) + ".zip",
    )
    registration_py_path = os.path.join(
        os.path.dirname(__file__),
        "registration.py",
    )
    if os.path.exists(github_code_download_zip_path) and not os.path.exists(
        registration_py_path
    ):
        import zipfile

        with zipfile.ZipFile(github_code_download_zip_path, "r") as z:
            z.extractall(os.path.dirname(__file__))

    # Lazy import to minimize initialization before blender version checking.
    from . import registration

    registration.register(bl_info["version"])


def unregister() -> None:
    import bpy

    if bpy.app.version < bl_info["blender"]:
        return

    # Lazy import to minimize initialization before blender version checking.
    from . import registration

    registration.unregister()


class glTF2ImportUserExtension:  # noqa: N801, SC200
    def __init__(self) -> None:
        # Lazy import to minimize initialization.
        from .importer.gltf2_addon_importer_user_extension import (
            Gltf2AddonImporterUserExtension,
        )

        self.user_extension = Gltf2AddonImporterUserExtension()

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/6f9d0d9fc1bb30e2b0bb019342ffe86bd67358fc/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L51
    def gather_import_image_after_hook(
        self, img: object, blender_image: object, gltf_importer: object
    ) -> None:
        self.user_extension.gather_import_image_after_hook(
            img, blender_image, gltf_importer
        )


class glTF2ExportUserExtension:  # noqa: N801, SC200
    def __init__(self) -> None:
        # Lazy import to minimize initialization.
        from .exporter.gltf2_addon_exporter_user_extension import (
            Gltf2AddonExporterUserExtension,
        )

        self.user_extension = Gltf2AddonExporterUserExtension()


if __name__ == "__main__":
    register()
