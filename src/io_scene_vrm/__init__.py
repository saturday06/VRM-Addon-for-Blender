# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP


from . import registration


def register() -> None:
    registration.register()


def unregister() -> None:
    registration.unregister()


class glTF2ImportUserExtension:
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


class glTF2ExportUserExtension:
    def __init__(self) -> None:
        # Lazy import to minimize initialization.
        from .exporter.gltf2_addon_exporter_user_extension import (
            Gltf2AddonExporterUserExtension,
        )

        self.user_extension = Gltf2AddonExporterUserExtension()

    # 3 arguments in Blender 2.93.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L68
    # 5 arguments in Blender 3.6.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/78c9556942e0780b471c9985e83e39e8c8d8f85a/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L84
    def gather_gltf_hook(
        self, a: object, b: object, c: object = None, d: object = None
    ) -> None:
        self.user_extension.gather_gltf_hook(a, b, c, d)


if __name__ == "__main__":
    register()
