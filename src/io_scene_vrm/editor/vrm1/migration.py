# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Armature, Context, Material, Object
from idprop.types import IDPropertyGroup
from mathutils import Vector

from ...common import convert, ops, shader
from ..extension import get_armature_extension
from .property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1MaterialColorBindPropertyGroup,
    Vrm1PropertyGroup,
)


def migrate_old_expression_layout(
    old_expression: object, expression: Vrm1ExpressionPropertyGroup
) -> None:
    if not isinstance(old_expression, IDPropertyGroup):
        return

    old_morph_target_binds = convert.iterator_or_none(
        old_expression.get("morph_target_binds")
    )
    if old_morph_target_binds is not None:
        for old_morph_target_bind in old_morph_target_binds:
            if not isinstance(old_morph_target_bind, IDPropertyGroup):
                continue

            morph_target_bind = expression.morph_target_binds.add()
            old_node = old_morph_target_bind.get("node")
            if isinstance(old_node, IDPropertyGroup):
                old_bpy_object = old_node.get("bpy_object")
                if isinstance(old_bpy_object, Object) and old_bpy_object.type == "MESH":
                    morph_target_bind.node.mesh_object_name = old_bpy_object.name
                old_node.clear()

            old_index = old_morph_target_bind.get("index")
            if isinstance(old_index, str):
                morph_target_bind.index = old_index

            old_weight = old_morph_target_bind.get("weight")
            if isinstance(old_weight, (float, int)):
                morph_target_bind.weight = old_weight

            old_morph_target_bind.clear()

    old_material_color_binds = convert.iterator_or_none(
        old_expression.get("material_color_binds")
    )
    if old_material_color_binds is not None:
        for old_material_color_bind in old_material_color_binds:
            if not isinstance(old_material_color_bind, IDPropertyGroup):
                continue

            material_color_bind = expression.material_color_binds.add()
            old_material = old_material_color_bind.get("material")
            if isinstance(old_material, Material):
                material_color_bind.material = old_material

            old_type = next(
                (
                    enum.identifier
                    for enum in Vrm1MaterialColorBindPropertyGroup.type_enum
                    if old_material_color_bind.get("type") == enum.value
                ),
                None,
            )
            if old_type is not None:
                material_color_bind.type = old_type

            old_target_value = shader.rgba_or_none(
                old_material_color_bind.get("target_value"), 0.0, 1.0
            )
            if old_target_value:
                material_color_bind.target_value = old_target_value

            old_material_color_bind.clear()

    old_texture_transform_binds = convert.iterator_or_none(
        old_expression.get("texture_transform_binds")
    )
    if old_texture_transform_binds is not None:
        for old_texture_transform_bind in old_texture_transform_binds:
            if not isinstance(old_texture_transform_bind, IDPropertyGroup):
                continue

            texture_transform_bind = expression.texture_transform_binds.add()
            old_material = old_texture_transform_bind.get("material")
            if isinstance(old_material, Material):
                texture_transform_bind.material = old_material

            old_scale = convert.float2_or_none(old_texture_transform_bind.get("scale"))
            if old_scale:
                texture_transform_bind.scale = old_scale

            old_offset = convert.float2_or_none(
                old_texture_transform_bind.get("offset")
            )
            if old_offset:
                texture_transform_bind.offset = old_offset

            old_texture_transform_bind.clear()

    old_is_binary = old_expression.get("is_binary")
    if isinstance(old_is_binary, int):
        expression.is_binary = bool(old_is_binary)

    old_override_blink = next(
        (
            enum.identifier
            for enum in Vrm1ExpressionPropertyGroup.expression_override_type_enum
            if old_expression.get("override_blink") == enum.value
        ),
        None,
    )
    if old_override_blink is not None:
        expression.override_blink = old_override_blink

    old_override_look_at = next(
        (
            enum.identifier
            for enum in Vrm1ExpressionPropertyGroup.expression_override_type_enum
            if old_expression.get("override_look_at") == enum.value
        ),
        None,
    )
    if old_override_look_at is not None:
        expression.override_look_at = old_override_look_at

    old_override_mouth = next(
        (
            enum.identifier
            for enum in Vrm1ExpressionPropertyGroup.expression_override_type_enum
            if old_expression.get("override_mouth") == enum.value
        ),
        None,
    )
    if old_override_mouth is not None:
        expression.override_mouth = old_override_mouth


def migrate_old_expressions_layout(expressions: Vrm1ExpressionsPropertyGroup) -> None:
    for name, expression in expressions.preset.name_to_expression_dict().items():
        property_name = {
            "blinkLeft": "blink_left",
            "blinkRight": "blink_right",
            "lookUp": "look_up",
            "lookDown": "look_down",
            "lookLeft": "look_left",
            "lookRight": "look_right",
        }.get(name)
        if property_name is None:
            property_name = name
        old_expression = expressions.get(property_name)
        migrate_old_expression_layout(old_expression, expression)
        expression.name = name
    for expression in expressions.custom:
        old_expression = expression.get("expression")
        migrate_old_expression_layout(old_expression, expression)


def migrate_pose(context: Context, armature: Object, armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 20, 34):
        return

    humanoid = ext.vrm1.humanoid
    if isinstance(humanoid.get("pose"), int):
        return

    if tuple(ext.addon_version) == ext.INITIAL_ADDON_VERSION:
        if "humanoid_params" in armature and "hips" in armature_data:
            humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier
        return

    action = humanoid.pose_library
    if action and action.name in context.blend_data.actions:
        humanoid.pose = humanoid.POSE_CUSTOM_POSE.identifier
    elif armature_data.pose_position == "REST":
        humanoid.pose = humanoid.POSE_REST_POSITION_POSE.identifier
    else:
        humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier


def migrate_auto_pose(_context: Context, armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) == ext.INITIAL_ADDON_VERSION or tuple(
        ext.addon_version
    ) >= (2, 20, 81):
        return

    humanoid = ext.vrm1.humanoid
    if not isinstance(humanoid.get("pose"), int):
        humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier


def migrate(context: Context, vrm1: Vrm1PropertyGroup, armature: Object) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    human_bones = vrm1.humanoid.human_bones
    human_bones.last_bone_names.clear()
    Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
    Vrm1HumanBonesPropertyGroup.update_all_node_candidates(context, armature_data.name)

    if human_bones.initial_automatic_bone_assignment:
        human_bones.initial_automatic_bone_assignment = False
        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
        if all(not b.node.bone_name for b in human_bone_name_to_human_bone.values()):
            ops.vrm.assign_vrm1_humanoid_human_bones_automatically(
                armature_name=armature.name
            )

    if tuple(get_armature_extension(armature_data).addon_version) <= (2, 14, 10):
        ext = get_armature_extension(armature_data)
        head_bone_name = ext.vrm1.humanoid.human_bones.head.node.bone_name
        head_bone = armature_data.bones.get(head_bone_name)
        if head_bone:
            look_at = get_armature_extension(armature_data).vrm1.look_at
            world_translation = (
                armature.matrix_world @ head_bone.matrix_local
            ).to_quaternion() @ Vector(look_at.offset_from_head_bone)
            look_at.offset_from_head_bone = list(world_translation)

    if tuple(get_armature_extension(armature_data).addon_version) <= (2, 15, 5):
        # Apply lower limit value
        look_at = get_armature_extension(armature_data).vrm1.look_at
        look_at.range_map_horizontal_inner.input_max_value = (
            look_at.range_map_horizontal_inner.input_max_value
        )
        look_at.range_map_horizontal_outer.input_max_value = (
            look_at.range_map_horizontal_outer.input_max_value
        )
        look_at.range_map_vertical_down.input_max_value = (
            look_at.range_map_vertical_down.input_max_value
        )
        look_at.range_map_vertical_up.input_max_value = (
            look_at.range_map_vertical_up.input_max_value
        )

    if tuple(get_armature_extension(armature_data).addon_version) < (2, 18, 0):
        migrate_old_expressions_layout(
            get_armature_extension(armature_data).vrm1.expressions
        )

    if tuple(get_armature_extension(armature_data).addon_version) < (2, 20, 0):
        look_at = get_armature_extension(armature_data).vrm1.look_at
        look_at.offset_from_head_bone = (
            look_at.offset_from_head_bone[0],
            look_at.offset_from_head_bone[2],
            -look_at.offset_from_head_bone[1],
        )

    migrate_pose(context, armature, armature_data)
    migrate_auto_pose(context, armature_data)

    # Expressionのプリセットに名前を設定する
    # 管理上は無くてもよいが、アニメーションキーフレームに表示されるので設定しておきたい
    expressions = get_armature_extension(armature_data).vrm1.expressions
    preset_name_to_expression_dict = expressions.preset.name_to_expression_dict()
    for preset_name, preset_expression in preset_name_to_expression_dict.items():
        if preset_expression.name != preset_name:
            preset_expression.name = preset_name

    Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
        context,
        armature_data.name,
        force=True,
    )
    ops.vrm.update_vrm1_expression_ui_list_elements()
