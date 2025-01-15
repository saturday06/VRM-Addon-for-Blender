# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.


import bpy


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def vrm(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filter_glob: str = "*.vrm",
    use_addon_preferences: bool = False,
    extract_textures_into_folder: bool = False,
    make_new_texture_folder: bool = True,
    set_shading_type_to_material_on_import: bool = True,
    set_view_transform_to_standard_on_import: bool = True,
    set_armature_display_to_wire: bool = True,
    set_armature_display_to_show_in_front: bool = True,
    set_armature_bone_shape_to_default: bool = True,
    enable_mtoon_outline_preview: bool = True,
    filepath: str = "",
) -> set[str]:
    return bpy.ops.import_scene.vrm(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        use_addon_preferences=use_addon_preferences,
        extract_textures_into_folder=extract_textures_into_folder,
        make_new_texture_folder=make_new_texture_folder,
        set_shading_type_to_material_on_import=set_shading_type_to_material_on_import,
        set_view_transform_to_standard_on_import=set_view_transform_to_standard_on_import,
        set_armature_display_to_wire=set_armature_display_to_wire,
        set_armature_display_to_show_in_front=set_armature_display_to_show_in_front,
        set_armature_bone_shape_to_default=set_armature_bone_shape_to_default,
        enable_mtoon_outline_preview=enable_mtoon_outline_preview,
        filepath=filepath,
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
) -> set[str]:
    return bpy.ops.import_scene.vrma(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        armature_object_name=armature_object_name,
        filepath=filepath,
    )
