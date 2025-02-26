# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.

from collections.abc import Mapping, Sequence
from typing import Optional, Union

import bpy


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def vrm(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filter_glob: str = "*.vrm",
    use_addon_preferences: bool = False,
    export_invisibles: bool = False,
    export_only_selections: bool = False,
    enable_advanced_preferences: bool = False,
    export_all_influences: bool = False,
    export_lights: bool = False,
    export_gltf_animations: bool = False,
    errors: Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]] = None,
    armature_object_name: str = "",
    ignore_warning: bool = False,
    filepath: str = "",
    check_existing: bool = True,
) -> set[str]:
    return bpy.ops.export_scene.vrm(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        use_addon_preferences=use_addon_preferences,
        export_invisibles=export_invisibles,
        export_only_selections=export_only_selections,
        enable_advanced_preferences=enable_advanced_preferences,
        export_all_influences=export_all_influences,
        export_lights=export_lights,
        export_gltf_animations=export_gltf_animations,
        errors=errors if errors is not None else [],
        armature_object_name=armature_object_name,
        ignore_warning=ignore_warning,
        filepath=filepath,
        check_existing=check_existing,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def vrma(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filter_glob: str = "*.vrma",
    armature_object_name: str = "",
    filepath: str = "",
    check_existing: bool = True,
) -> set[str]:
    return bpy.ops.export_scene.vrma(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        armature_object_name=armature_object_name,
        filepath=filepath,
        check_existing=check_existing,
    )
