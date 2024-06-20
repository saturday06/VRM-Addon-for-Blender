# This code is auto generated.
# `poetry run python tools/property_typing.py`

from collections.abc import Mapping, Sequence
from typing import Optional, Union

import bpy


def vrma_import_prerequisite(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_object_name: str = "",
    armature_object_name_candidates: Optional[
        Sequence[Mapping[str, Union[str, int, float, bool]]]
    ] = None,
) -> set[str]:
    return bpy.ops.wm.vrma_import_prerequisite(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_object_name=armature_object_name,
        armature_object_name_candidates=armature_object_name_candidates
        if armature_object_name_candidates is not None
        else [],
    )


def vrm_license_warning(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    license_confirmations: Optional[
        Sequence[Mapping[str, Union[str, int, float, bool]]]
    ] = None,
    import_anyway: bool = False,
    extract_textures_into_folder: bool = False,
    make_new_texture_folder: bool = False,
    set_shading_type_to_material_on_import: bool = False,
    set_view_transform_to_standard_on_import: bool = False,
    set_armature_display_to_wire: bool = False,
    set_armature_display_to_show_in_front: bool = False,
    set_armature_bone_shape_to_default: bool = False,
) -> set[str]:
    return bpy.ops.wm.vrm_license_warning(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filepath=filepath,
        license_confirmations=license_confirmations
        if license_confirmations is not None
        else [],
        import_anyway=import_anyway,
        extract_textures_into_folder=extract_textures_into_folder,
        make_new_texture_folder=make_new_texture_folder,
        set_shading_type_to_material_on_import=set_shading_type_to_material_on_import,
        set_view_transform_to_standard_on_import=set_view_transform_to_standard_on_import,
        set_armature_display_to_wire=set_armature_display_to_wire,
        set_armature_display_to_show_in_front=set_armature_display_to_show_in_front,
        set_armature_bone_shape_to_default=set_armature_bone_shape_to_default,
    )


def vrma_export_prerequisite(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_object_name: str = "",
    armature_object_name_candidates: Optional[
        Sequence[Mapping[str, Union[str, int, float, bool]]]
    ] = None,
) -> set[str]:
    return bpy.ops.wm.vrma_export_prerequisite(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_object_name=armature_object_name,
        armature_object_name_candidates=armature_object_name_candidates
        if armature_object_name_candidates is not None
        else [],
    )


def vrm_export_armature_selection(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_object_name: str = "",
    armature_object_name_candidates: Optional[
        Sequence[Mapping[str, Union[str, int, float, bool]]]
    ] = None,
) -> set[str]:
    return bpy.ops.wm.vrm_export_armature_selection(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_object_name=armature_object_name,
        armature_object_name_candidates=armature_object_name_candidates
        if armature_object_name_candidates is not None
        else [],
    )


def vrm_export_confirmation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    errors: Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]] = None,
    armature_object_name: str = "",
    export_anyway: bool = False,
) -> set[str]:
    return bpy.ops.wm.vrm_export_confirmation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        errors=errors if errors is not None else [],
        armature_object_name=armature_object_name,
        export_anyway=export_anyway,
    )


def vrm_export_human_bones_assignment(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_object_name: str = "",
) -> set[str]:
    return bpy.ops.wm.vrm_export_human_bones_assignment(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_object_name=armature_object_name,
    )


def vrm_gltf2_addon_disabled_warning(
    execution_context: str = "EXEC_DEFAULT",
) -> set[str]:
    return bpy.ops.wm.vrm_gltf2_addon_disabled_warning(  # type: ignore[attr-defined, no-any-return]
        execution_context,
    )
