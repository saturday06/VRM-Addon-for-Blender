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
    "version": (2, 1, 3),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import-Edit-Export VRM",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "https://github.com/saturday06/VRM_Addon_for_Blender/issues",
    "category": "Import-Export",
}


def register() -> None:
    import bpy

    if bpy.app.version < bl_info["blender"]:
        raise Exception(
            f"This add-on doesn't support Blender version less than {bl_info['blender']} "
            + f"but the current version is {bpy.app.version}"
        )

    # Lazy import to minimize initialization before blender version checking and reload_package().
    # 'import io_scene_vrm' causes an error in blender and vscode mypy integration.
    # pylint: disable=import-self,no-name-in-module
    from .io_scene_vrm import registration

    # pylint: enable=import-self,no-name-in-module

    registration.register(bl_info["version"])


def unregister() -> None:
    import bpy

    if bpy.app.version < bl_info["blender"]:
        return

    # Lazy import to minimize initialization before blender version checking and reload_package().
    # 'import io_scene_vrm' causes an error in blender and vscode mypy integration.
    # pylint: disable=import-self,no-name-in-module
    from .io_scene_vrm import registration

    # pylint: enable=import-self,no-name-in-module

    registration.unregister()


class glTF2ExportUserExtension:  # noqa: N801, SC200
    def __init__(self) -> None:
        # Lazy import to minimize initialization before blender version checking and reload_package().
        # 'import io_scene_vrm' causes an error in blender and vscode mypy integration.
        # pylint: disable=import-self,no-name-in-module
        from .io_scene_vrm.exporter.user_extension import UserExtension

        self.user_extension = UserExtension()

    def gather_skin_hook(
        self, gltf2_object: object, blender_object: object, export_settings: object
    ) -> None:
        self.user_extension.gather_skin_hook(
            gltf2_object, blender_object, export_settings
        )


if __name__ == "__main__":
    register()
