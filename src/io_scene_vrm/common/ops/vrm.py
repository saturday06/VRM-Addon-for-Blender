# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.

from collections.abc import Mapping, Sequence
from typing import Optional, Union

import bpy


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_material_value_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_material_value_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_material_value_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    material_value_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_material_value_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        material_value_index=material_value_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_material_value_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    material_value_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_material_value_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        material_value_index=material_value_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_material_value_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    material_value_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_material_value_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        material_value_index=material_value_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_material_value_bind_target_value(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    material_value_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_material_value_bind_target_value(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        material_value_index=material_value_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_material_value_bind_target_value(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    material_value_index: int = 0,
    target_value_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_material_value_bind_target_value(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        material_value_index=material_value_index,
        target_value_index=target_value_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_blend_shape_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_blend_shape_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        name=name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_blend_shape_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_blend_shape_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_blend_shape_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_blend_shape_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_blend_shape_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_blend_shape_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_blend_shape_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_blend_shape_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_blend_shape_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_blend_shape_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_blend_shape_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_blend_shape_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_blend_shape_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_blend_shape_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_secondary_animation_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    bone_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_secondary_animation_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        bone_name=bone_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_secondary_animation_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_secondary_animation_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_secondary_animation_collider_group_coll(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_secondary_animation_collider_group_coll(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_secondary_animation_collider_group_coll(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_secondary_animation_collider_group_coll(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_secondary_animation_group_bone(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_secondary_animation_group_bone(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_secondary_animation_group_bone(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    bone_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_secondary_animation_group_bone(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        bone_index=bone_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_secondary_animation_group_bone(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    bone_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_secondary_animation_group_bone(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        bone_index=bone_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_secondary_animation_group_bone(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    bone_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_secondary_animation_group_bone(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        bone_index=bone_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_secondary_animation_group_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_secondary_animation_group_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_secondary_animation_group_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_secondary_animation_group_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_secondary_animation_group_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_secondary_animation_group_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_secondary_animation_group_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_secondary_animation_group_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_secondary_animation_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    blend_shape_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_secondary_animation_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        blend_shape_group_index=blend_shape_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_secondary_animation_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_secondary_animation_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_secondary_animation_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_secondary_animation_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_secondary_animation_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    bone_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_secondary_animation_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        bone_group_index=bone_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm0_secondary_animation_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm0_secondary_animation_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm0_secondary_animation_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm0_secondary_animation_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm0_secondary_animation_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm0_secondary_animation_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm0_secondary_animation_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm0_secondary_animation_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def assign_vrm0_humanoid_human_bones_automatically(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.assign_vrm0_humanoid_human_bones_automatically(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_meta_author(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_meta_author(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_meta_author(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    author_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_meta_author(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        author_index=author_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_meta_author(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    author_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_meta_author(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        author_index=author_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_meta_author(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    author_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_meta_author(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        author_index=author_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_meta_reference(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_meta_reference(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_meta_reference(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    reference_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_meta_reference(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        reference_index=reference_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_meta_reference(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    reference_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_meta_reference(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        reference_index=reference_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_meta_reference(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    reference_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_meta_reference(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        reference_index=reference_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_expressions_custom_expression(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    custom_expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_expressions_custom_expression(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        custom_expression_name=custom_expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_expressions_custom_expression(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    custom_expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_expressions_custom_expression(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        custom_expression_name=custom_expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_expressions_custom_expression(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    custom_expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_expressions_custom_expression(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        custom_expression_name=custom_expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_expressions_custom_expression(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    custom_expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_expressions_custom_expression(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        custom_expression_name=custom_expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_expression_morph_target_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_expression_morph_target_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_expression_morph_target_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_expression_morph_target_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_expression_morph_target_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_expression_morph_target_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_expression_morph_target_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_expression_morph_target_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_expression_material_color_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_expression_material_color_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_expression_material_color_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_expression_material_color_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_expression_material_color_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_expression_material_color_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_expression_material_color_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_expression_material_color_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_expression_texture_transform_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_expression_texture_transform_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_expression_texture_transform_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_expression_texture_transform_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_expression_texture_transform_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_expression_texture_transform_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_expression_texture_transform_bind(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
    bind_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_expression_texture_transform_bind(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
        bind_index=bind_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_vrm1_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_vrm1_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_vrm1_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_vrm1_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_vrm1_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_vrm1_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_vrm1_first_person_mesh_annotation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    mesh_annotation_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_vrm1_first_person_mesh_annotation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        mesh_annotation_index=mesh_annotation_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def assign_vrm1_humanoid_human_bones_automatically(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.assign_vrm1_humanoid_human_bones_automatically(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def update_vrm1_expression_ui_list_elements(
    execution_context: str = "EXEC_DEFAULT",
) -> set[str]:
    return bpy.ops.vrm.update_vrm1_expression_ui_list_elements(  # type: ignore[attr-defined, no-any-return]
        execution_context,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def refresh_vrm1_expression_texture_transform_bind_preview(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    expression_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.refresh_vrm1_expression_texture_transform_bind_preview(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        expression_name=expression_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    collider_group_index: int = 0,
    collider_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_collider_group_collider(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        collider_group_index=collider_group_index,
        collider_index=collider_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_spring(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_spring(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_spring(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_spring(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_spring(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_spring(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_spring(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_spring(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_spring_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_spring_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_spring_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_spring_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_spring_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_spring_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_spring_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    collider_group_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_spring_collider_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        collider_group_index=collider_group_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def add_spring_bone1_spring_joint(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    guess_properties: bool = False,
) -> set[str]:
    return bpy.ops.vrm.add_spring_bone1_spring_joint(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        guess_properties=guess_properties,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def remove_spring_bone1_spring_joint(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    joint_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.remove_spring_bone1_spring_joint(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        joint_index=joint_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_up_spring_bone1_joint(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    joint_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_up_spring_bone1_joint(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        joint_index=joint_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def move_down_spring_bone1_joint(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
    spring_index: int = 0,
    joint_index: int = 0,
) -> set[str]:
    return bpy.ops.vrm.move_down_spring_bone1_joint(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
        spring_index=spring_index,
        joint_index=joint_index,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def reset_spring_bone1_animation_state(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.reset_spring_bone1_animation_state(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def update_spring_bone1_animation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    delta_time: float = 0.0,
) -> set[str]:
    return bpy.ops.vrm.update_spring_bone1_animation(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        delta_time=delta_time,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def convert_material_to_mtoon1(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.convert_material_to_mtoon1(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        material_name=material_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def convert_mtoon1_to_bsdf_principled(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.convert_mtoon1_to_bsdf_principled(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        material_name=material_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def reset_mtoon1_material_shader_node_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.reset_mtoon1_material_shader_node_group(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        material_name=material_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def import_mtoon1_texture_image_file(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.bmp;*.sgi;*.bw;*.rgb;*.rgba;*.png;*.jpg;*.jpeg;*.jp2;*.tga;*."
    "cin;*.dpx;*.exr;*.hdr;*.tif;*.tiff",
    material_name: str = "",
    target_texture: str = "",
) -> set[str]:
    return bpy.ops.vrm.import_mtoon1_texture_image_file(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filepath=filepath,
        filter_glob=filter_glob,
        material_name=material_name,
        target_texture=target_texture,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def refresh_mtoon1_outline(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str = "",
    create_modifier: bool = False,
) -> set[str]:
    return bpy.ops.vrm.refresh_mtoon1_outline(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        material_name=material_name,
        create_modifier=create_modifier,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def show_material_blender_4_2_warning(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name_lines: str = "",
) -> set[str]:
    return bpy.ops.vrm.show_material_blender_4_2_warning(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        material_name_lines=material_name_lines,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def bones_rename(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.bones_rename(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def open_url_in_web_browser(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    url: str = "",
) -> set[str]:
    return bpy.ops.vrm.open_url_in_web_browser(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        url=url,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def save_human_bone_mappings(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filter_glob: str = "*.json",
    filepath: str = "",
    check_existing: bool = True,
) -> set[str]:
    return bpy.ops.vrm.save_human_bone_mappings(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        filepath=filepath,
        check_existing=check_existing,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def load_human_bone_mappings(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filter_glob: str = "*.json",
    filepath: str = "",
) -> set[str]:
    return bpy.ops.vrm.load_human_bone_mappings(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filter_glob=filter_glob,
        filepath=filepath,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def show_blend_file_compatibility_warning(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    file_version: str = "",
    app_version: str = "",
) -> set[str]:
    return bpy.ops.vrm.show_blend_file_compatibility_warning(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        file_version=file_version,
        app_version=app_version,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def show_blend_file_addon_compatibility_warning(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    file_addon_version: str = "",
    installed_addon_version: str = "",
) -> set[str]:
    return bpy.ops.vrm.show_blend_file_addon_compatibility_warning(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        file_addon_version=file_addon_version,
        installed_addon_version=installed_addon_version,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def make_estimated_humanoid_t_pose(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.make_estimated_humanoid_t_pose(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        armature_name=armature_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def model_validate(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    show_successful_message: bool = True,
    errors: Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]] = None,
    armature_object_name: str = "",
) -> set[str]:
    return bpy.ops.vrm.model_validate(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        show_successful_message=show_successful_message,
        errors=errors if errors is not None else [],
        armature_object_name=armature_object_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def import_vrm_via_file_handler(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
) -> set[str]:
    return bpy.ops.vrm.import_vrm_via_file_handler(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filepath=filepath,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def import_vrma_via_file_handler(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
) -> set[str]:
    return bpy.ops.vrm.import_vrma_via_file_handler(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        filepath=filepath,
    )
