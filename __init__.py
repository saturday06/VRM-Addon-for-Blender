"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

#
#
# Please don't import anything before "bl_info" assignment and reload_package().
#
#


# Script reloading (if the user calls 'Reload Scripts' from Blender)
# https://github.com/KhronosGroup/glTF-Blender-IO/blob/04e26bef903543d08947c5a9a5fea4e787b68f17/addons/io_scene_gltf2/__init__.py#L32-L54
# http://www.apache.org/licenses/LICENSE-2.0
def reload_package(module_dict_main: dict) -> None:  # type: ignore[type-arg]
    # Lazy import to minimize initialization before reload_package()
    import importlib
    from pathlib import Path
    from typing import Any, Dict

    def reload_package_recursive(
        current_dir: Path, module_dict: Dict[str, Any]
    ) -> None:
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue

            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)


# Place it before "bl_info" to detect script reloading.
if "bl_info" in locals():
    reload_package(locals())

# Place it after "if "bl_info" in locals():" to detect script reloading.
bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (1, 3, 1),
    "blender": (2, 82, 0),
    "location": "File > Import-Export",
    "description": "Import-Edit-Export VRM",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "https://github.com/saturday06/VRM_Addon_for_Blender/issues",
    "category": "Import-Export",
}


def register() -> None:
    # Lazy import to minimize initialization before reload_package()
    # 'import io_scene_vrm' causes error in blender and vscode mypy integration
    # pylint: disable=no-name-in-module
    from . import io_scene_vrm  # type: ignore[attr-defined]

    io_scene_vrm.register(bl_info.get("version"))


def unregister() -> None:
    # Lazy import to minimize initialization before reload_package()
    # 'import io_scene_vrm' causes error in blender and vscode mypy integration
    # pylint: disable=no-name-in-module
    from . import io_scene_vrm  # type: ignore[attr-defined]

    io_scene_vrm.unregister()


if __name__ == "__main__":
    register()
