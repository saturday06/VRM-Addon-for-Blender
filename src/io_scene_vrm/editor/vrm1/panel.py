# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet

import bpy
from bpy.app.translations import pgettext
from bpy.types import Armature, Context, Mesh, Object, Panel, UILayout

from ...common.logger import get_logger
from ...common.vrm1.human_bone import HumanBoneSpecifications
from .. import ops, search
from ..extension import get_armature_extension, get_bone_extension
from ..migration import defer_migrate
from ..ops import layout_operator
from ..panel import VRM_PT_vrm_armature_object_property, draw_template_list
from ..search import active_object_is_vrm1_armature
from . import ops as vrm1_ops
from .property_group import (
    Vrm1CustomExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanBonePropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MaterialColorBindPropertyGroup,
    Vrm1MetaPropertyGroup,
    Vrm1MorphTargetBindPropertyGroup,
    Vrm1TextureTransformBindPropertyGroup,
)
from .ui_list import (
    VRM_UL_vrm1_expression,
    VRM_UL_vrm1_first_person_mesh_annotation,
    VRM_UL_vrm1_material_color_bind,
    VRM_UL_vrm1_meta_author,
    VRM_UL_vrm1_meta_reference,
    VRM_UL_vrm1_morph_target_bind,
    VRM_UL_vrm1_texture_transform_bind,
)

logger = get_logger(__name__)


def draw_vrm1_bone_prop_search(
    layout: UILayout,
    human_bone: Vrm1HumanBonePropertyGroup,
    icon: str,
) -> None:
    layout.prop_search(
        human_bone.node,
        "bone_name",
        human_bone,
        "node_candidates",
        text="",
        translate=False,
        icon=icon,
    )


def draw_vrm1_humanoid_required_bones_layout(
    human_bones: Vrm1HumanBonesPropertyGroup,
    layout: UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="VRM Required Bones", icon="ARMATURE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text=HumanBoneSpecifications.HEAD.label)
    column.label(text=HumanBoneSpecifications.SPINE.label)
    column.label(text=HumanBoneSpecifications.HIPS.label)
    column = row.column(align=True)
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones.head, icon)
    draw_vrm1_bone_prop_search(column, human_bones.spine, icon)
    draw_vrm1_bone_prop_search(column, human_bones.hips, icon)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text="")
    column.label(text=HumanBoneSpecifications.LEFT_UPPER_ARM.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_LOWER_ARM.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_HAND.label_no_left_right)
    column.separator()
    column.label(text=HumanBoneSpecifications.LEFT_UPPER_LEG.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_LOWER_LEG.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_FOOT.label_no_left_right)

    column = row.column(align=True)
    column.label(text="Right")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones.right_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones.right_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_foot, icon)

    column = row.column(align=True)
    column.label(text="Left")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones.left_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones.left_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_foot, icon)


def draw_vrm1_humanoid_optional_bones_layout(
    human_bones: Vrm1HumanBonesPropertyGroup,
    layout: UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="VRM Optional Bones", icon="BONE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    icon = "HIDE_OFF"
    label_column = row.column(align=True)
    label_column.label(text="")
    label_column.label(text=HumanBoneSpecifications.LEFT_EYE.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.JAW.label)
    label_column.label(text=HumanBoneSpecifications.NECK.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_SHOULDER.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.UPPER_CHEST.label)
    label_column.label(text=HumanBoneSpecifications.CHEST.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_TOES.label_no_left_right)

    search_column = row.column(align=True)

    right_left_row = search_column.row(align=True)
    right_left_row.label(text="Right")
    right_left_row.label(text="Left")

    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_eye, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_eye, icon)

    icon = "USER"
    draw_vrm1_bone_prop_search(search_column, human_bones.jaw, icon)
    draw_vrm1_bone_prop_search(search_column, human_bones.neck, icon)

    icon = "VIEW_PAN"
    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_shoulder, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_shoulder, icon)

    icon = "USER"
    draw_vrm1_bone_prop_search(search_column, human_bones.upper_chest, icon)
    draw_vrm1_bone_prop_search(search_column, human_bones.chest, icon)

    icon = "MOD_DYNAMICPAINT"
    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_toes, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_toes, icon)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text="", translate=False)
    column.label(text="Left Thumb:")
    column.label(text="Left Index:")
    column.label(text="Left Middle:")
    column.label(text="Left Ring:")
    column.label(text="Left Little:")
    column.separator()
    column.label(text="Right Thumb:")
    column.label(text="Right Index:")
    column.label(text="Right Middle:")
    column.label(text="Right Ring:")
    column.label(text="Right Little:")

    icon = "VIEW_PAN"
    column = row.column(align=True)
    column.label(text="Root")
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_metacarpal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_proximal, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_metacarpal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_proximal, icon)

    column = row.column(align=True)
    column.label(text="", translate=False)
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_intermediate, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_intermediate, icon)

    column = row.column(align=True)
    column.label(text="Tip")
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_distal, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_distal, icon)


def draw_vrm1_humanoid_layout(
    context: Context,
    armature: Object,
    layout: UILayout,
    humanoid: Vrm1HumanoidPropertyGroup,
) -> None:
    if defer_migrate(armature.name):
        data = armature.data
        if not isinstance(data, Armature):
            return
        Vrm1HumanBonesPropertyGroup.defer_update_all_node_candidates(data.name)

    data = armature.data
    if not isinstance(data, Armature):
        return
    human_bones = humanoid.human_bones

    armature_box = layout

    t_pose_box = armature_box.box()
    column = t_pose_box.row().column()
    column.label(text="VRM T-Pose", icon="OUTLINER_OB_ARMATURE")
    column.prop(humanoid, "pose")
    if humanoid.pose == humanoid.POSE_CUSTOM_POSE.identifier:
        label = "Pose Library" if bpy.app.version < (3, 0) else "Pose Asset"
        column.prop_search(
            humanoid,
            "pose_library",
            context.blend_data,
            "actions",
            text=label,
            translate=False,
        )
        if humanoid.pose_library and humanoid.pose_library.pose_markers:
            column.prop_search(
                humanoid,
                "pose_marker_name",
                humanoid.pose_library,
                "pose_markers",
                text="Pose",
                translate=False,
            )

    bone_operator_column = layout.column()
    layout_operator(
        bone_operator_column,
        vrm1_ops.VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
        icon="ARMATURE_DATA",
    ).armature_name = armature.name

    if ops.VRM_OT_simplify_vroid_bones.vroid_bones_exist(data):
        simplify_vroid_bones_op = layout_operator(
            armature_box,
            ops.VRM_OT_simplify_vroid_bones,
            text=pgettext(ops.VRM_OT_simplify_vroid_bones.bl_label),
            icon="GREASEPENCIL",
        )
        simplify_vroid_bones_op.armature_name = armature.name

    draw_vrm1_humanoid_required_bones_layout(human_bones, armature_box.box())
    draw_vrm1_humanoid_optional_bones_layout(human_bones, armature_box.box())

    non_humanoid_export_column = layout.column()
    non_humanoid_export_column.prop(human_bones, "allow_non_humanoid_rig")
    if human_bones.allow_non_humanoid_rig:
        non_humanoid_warnings_box = non_humanoid_export_column.box()
        non_humanoid_warnings_column = non_humanoid_warnings_box.column(align=True)
        text = pgettext(
            "VRMs exported as Non-Humanoid\n"
            + "Rigs can not have animations applied\n"
            + "for humanoid avatars."
        )
        for index, message in enumerate(pgettext(text).splitlines()):
            non_humanoid_warnings_column.label(
                text=message,
                translate=False,
                icon="ERROR" if index == 0 else "NONE",
            )


class VRM_PT_vrm1_humanoid_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_humanoid_armature_object_property"
    bl_label = "Humanoid"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_humanoid_layout(
            context,
            active_object,
            self.layout,
            get_armature_extension(armature_data).vrm1.humanoid,
        )


class VRM_PT_vrm1_humanoid_ui(Panel):
    bl_idname = "VRM_PT_vrm1_humanoid_ui"
    bl_label = "Humanoid"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_humanoid_layout(
            context,
            armature,
            self.layout,
            get_armature_extension(armature_data).vrm1.humanoid,
        )


def draw_vrm1_first_person_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    first_person: Vrm1FirstPersonPropertyGroup,
) -> None:
    defer_migrate(armature.name)
    column = layout.column()
    column.label(text="Mesh Annotations", icon="FULLSCREEN_EXIT")

    (
        mesh_annotation_collection_ops,
        mesh_annotation_collection_item_ops,
        mesh_annotation_index,
        _,
        _,
    ) = draw_template_list(
        column,
        VRM_UL_vrm1_first_person_mesh_annotation.bl_idname,
        first_person,
        "mesh_annotations",
        "active_mesh_annotation_index",
        vrm1_ops.VRM_OT_add_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_remove_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_move_up_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_move_down_vrm1_first_person_mesh_annotation,
    )

    for mesh_annotation_collection_op in mesh_annotation_collection_ops:
        mesh_annotation_collection_op.armature_name = armature.name

    for mesh_annotation_collection_item_op in mesh_annotation_collection_item_ops:
        mesh_annotation_collection_item_op.mesh_annotation_index = mesh_annotation_index


class VRM_PT_vrm1_first_person_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_first_person_armature_object_property"
    bl_label = "First Person"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_first_person_layout(
            active_object,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.first_person,
        )


class VRM_PT_vrm1_first_person_ui(Panel):
    bl_idname = "VRM_PT_vrm1_first_person_ui"
    bl_label = "First Person"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="USER")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_first_person_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.first_person,
        )


def draw_vrm1_look_at_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    look_at: Vrm1LookAtPropertyGroup,
) -> None:
    defer_migrate(armature.name)

    layout.prop(look_at, "enable_preview")

    label_input_split = layout.split(factor=0.4)
    label_column = label_input_split.column()
    label_column.label(text="Preview Target:")
    label_column.label(text="Type:")
    input_column = label_input_split.column()
    input_column.prop(look_at, "preview_target_bpy_object", text="", translate=False)
    input_column.prop(look_at, "type", text="", translate=False)

    offset_from_head_bone_column = layout.column()
    offset_from_head_bone_column.label(text="Offset from Head Bone:")
    offset_from_head_bone_column.row().prop(
        look_at, "offset_from_head_bone", icon="BONE_DATA", text="", translate=False
    )

    column = layout.box().column(align=True)
    column.label(text="Range Map Horizontal Inner", icon="FULLSCREEN_EXIT")
    column.prop(look_at.range_map_horizontal_inner, "input_max_value")
    column.prop(look_at.range_map_horizontal_inner, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Horizontal Outer", icon="FULLSCREEN_ENTER")
    column.prop(look_at.range_map_horizontal_outer, "input_max_value")
    column.prop(look_at.range_map_horizontal_outer, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Vertical Up", icon="TRIA_UP")
    column.prop(look_at.range_map_vertical_up, "input_max_value")
    column.prop(look_at.range_map_vertical_up, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Vertical Down", icon="TRIA_DOWN")
    column.prop(look_at.range_map_vertical_down, "input_max_value")
    column.prop(look_at.range_map_vertical_down, "output_scale")


class VRM_PT_vrm1_look_at_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_look_at_armature_object_property"
    bl_label = "Look At"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_look_at_layout(
            active_object,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.look_at,
        )


class VRM_PT_vrm1_look_at_ui(Panel):
    bl_idname = "VRM_PT_vrm1_look_at_ui"
    bl_label = "Look At"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_look_at_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.look_at,
        )


def draw_vrm1_expressions_morph_target_bind_layout(
    context: Context,
    layout: UILayout,
    bind: Vrm1MorphTargetBindPropertyGroup,
) -> None:
    blend_data = context.blend_data

    bind_column = layout.column()

    bind_column.prop(
        bind.node,
        "bpy_object",
        text="Mesh",
        icon="OUTLINER_OB_MESH",
    )
    mesh_object = blend_data.objects.get(bind.node.mesh_object_name)
    if not mesh_object:
        return
    mesh = mesh_object.data
    if not isinstance(mesh, Mesh):
        return
    shape_keys = mesh.shape_keys
    if not shape_keys:
        return
    key_blocks = shape_keys.key_blocks
    if not key_blocks:
        return

    bind_column.prop_search(
        bind,
        "index",
        shape_keys,
        "key_blocks",
        text="Shape key",
    )
    bind_column.prop(bind, "weight", slider=True)


def draw_vrm1_expressions_material_color_bind_layout(
    context: Context,
    layout: UILayout,
    bind: Vrm1MaterialColorBindPropertyGroup,
) -> None:
    blend_data = context.blend_data

    bind_column = layout.column()
    bind_column.prop_search(bind, "material", blend_data, "materials")
    bind_column.prop(bind, "type")
    target_value_split = bind_column.split(factor=0.5)
    target_value_split.label(text="Target Value:")
    if bind.type == "color":
        target_value_split.prop(bind, "target_value", text="", translate=False)
    else:
        target_value_split.prop(bind, "target_value_as_rgb", text="", translate=False)


def draw_vrm1_expressions_texture_transform_bind_layout(
    context: Context,
    layout: UILayout,
    bind: Vrm1TextureTransformBindPropertyGroup,
) -> None:
    if not bind.show_experimental_preview_feature:
        blend_data = context.blend_data
        bind_column = layout.column()
        bind_column.prop_search(bind, "material", blend_data, "materials")
        bind_column.prop(bind, "scale")
        bind_column.prop(bind, "offset")
        if bpy.app.version < (4, 2):
            return
        bind_column.separator()
        bind_column.prop(bind, "show_experimental_preview_feature")
        return

    bind_column = layout.column()
    bind_column.prop(bind, "show_experimental_preview_feature")

    # Find the armature object
    armature = search.current_armature(context)
    if not armature:
        layout.label(text="No VRM Armature found in the scene", icon="ERROR")
        return
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        layout.label(text="Invalid armature data", icon="ERROR")
        return

    try:
        extension = get_armature_extension(armature_data)
        vrm1 = extension.vrm1
        expressions = vrm1.expressions

        all_expressions = list(expressions.all_name_to_expression_dict().values())
        if (
            0
            <= expressions.active_expression_ui_list_element_index
            < len(all_expressions)
        ):
            active_expression = all_expressions[
                expressions.active_expression_ui_list_element_index
            ]
            if isinstance(active_expression, Vrm1CustomExpressionPropertyGroup):
                expression_name = active_expression.custom_name
            else:
                expression_name = active_expression.name
        else:
            expression_name = ""
    except TypeError:
        layout.label(text="Invalid VRM extension", icon="ERROR")
        return

    # Add refresh preview button
    refresh_row = bind_column.row()
    refresh_op = layout_operator(
        refresh_row,
        vrm1_ops.VRM_OT_refresh_vrm1_expression_texture_transform_bind_preview,
        text="Refresh Preview",
        icon="FILE_REFRESH",
    )
    refresh_op.armature_name = armature.name
    refresh_op.expression_name = expression_name

    bind_column.separator()

    bind_column.prop_search(bind, "material", context.blend_data, "materials")
    # Only show scale, and offset properties if there's a valid bind
    if bind and bind.material:
        bind_column.prop(bind, "scale")
        bind_column.prop(bind, "offset")
    else:
        bind_column.label(text="No texture transform bind for this expression")


def draw_vrm1_expressions_layout(
    armature: Object,
    context: Context,
    layout: UILayout,
    expressions: Vrm1ExpressionsPropertyGroup,
) -> None:
    defer_migrate(armature.name)

    preset_expressions = list(expressions.preset.name_to_expression_dict().values())

    (
        expression_collection_ops,
        expression_collection_item_ops,
        expression_ui_list_element_index,
        _,
        _,
    ) = draw_template_list(
        layout,
        VRM_UL_vrm1_expression.bl_idname,
        expressions,
        "expression_ui_list_elements",
        "active_expression_ui_list_element_index",
        vrm1_ops.VRM_OT_add_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_remove_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_move_up_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_move_down_vrm1_expressions_custom_expression,
        can_remove=lambda active_collection_index: (
            active_collection_index >= len(preset_expressions)
        ),
        can_move=lambda active_collection_index: (
            len(expressions.custom) >= 2
            and active_collection_index >= len(preset_expressions)
        ),
    )

    for expression_collection_op in expression_collection_ops:
        expression_collection_op.armature_name = armature.name
        expression_collection_op.custom_expression_name = "custom"

    custom_index = expression_ui_list_element_index - len(preset_expressions)

    if 0 <= expression_ui_list_element_index < len(preset_expressions):
        expression = preset_expressions[expression_ui_list_element_index]
        preset_icon = expressions.preset.get_icon(expression.name)
        if not preset_icon:
            logger.error("Unknown preset expression: %s", expression.name)
            preset_icon = "SHAPEKEY_DATA"
        layout.label(text=expression.name, translate=False, icon=preset_icon)
    elif 0 <= custom_index < len(expressions.custom):
        expression = expressions.custom[custom_index]

        for expression_collection_item_op in expression_collection_item_ops:
            expression_collection_item_op.custom_expression_name = (
                expression.custom_name
            )

        layout.prop(expression, "custom_name")
    else:
        return

    column = layout.column()
    column.prop(expression, "preview", icon="PLAY", text="Preview")
    column.prop(expression, "is_binary", icon="IPO_CONSTANT")
    column.prop(expression, "override_blink")
    column.prop(expression, "override_look_at")
    column.prop(expression, "override_mouth")
    column.separator(factor=0.5)

    morph_target_binds_box = column.box()
    morph_target_binds_box.label(text="Morph Target Binds", icon="MESH_DATA")

    (
        morph_target_bind_collection_ops,
        morph_target_bind_collection_item_ops,
        morph_target_bind_index,
        morph_target_bind,
        _,
    ) = draw_template_list(
        morph_target_binds_box,
        VRM_UL_vrm1_morph_target_bind.bl_idname,
        expression,
        "morph_target_binds",
        "active_morph_target_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_morph_target_bind,
    )

    for morph_target_bind_collection_op in morph_target_bind_collection_ops:
        morph_target_bind_collection_op.armature_name = armature.name
        morph_target_bind_collection_op.expression_name = expression.name

    for morph_target_bind_collection_item_op in morph_target_bind_collection_item_ops:
        morph_target_bind_collection_item_op.bind_index = morph_target_bind_index

    if isinstance(morph_target_bind, Vrm1MorphTargetBindPropertyGroup):
        draw_vrm1_expressions_morph_target_bind_layout(
            context,
            morph_target_binds_box,
            morph_target_bind,
        )

    column.separator(factor=0.2)

    material_color_binds_box = column.box()
    material_color_binds_box.label(text="Material Color Binds", icon="MATERIAL")

    (
        material_color_bind_collection_ops,
        material_color_bind_collection_item_ops,
        material_color_bind_index,
        material_color_bind,
        _,
    ) = draw_template_list(
        material_color_binds_box,
        VRM_UL_vrm1_material_color_bind.bl_idname,
        expression,
        "material_color_binds",
        "active_material_color_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_material_color_bind,
    )

    for material_color_bind_collection_op in material_color_bind_collection_ops:
        material_color_bind_collection_op.armature_name = armature.name
        material_color_bind_collection_op.expression_name = expression.name

    for (
        material_color_bind_collection_item_op
    ) in material_color_bind_collection_item_ops:
        material_color_bind_collection_item_op.bind_index = material_color_bind_index

    if isinstance(material_color_bind, Vrm1MaterialColorBindPropertyGroup):
        draw_vrm1_expressions_material_color_bind_layout(
            context,
            material_color_binds_box,
            material_color_bind,
        )
    column.separator(factor=0.2)

    texture_transform_binds_box = column.box()
    texture_transform_binds_box.label(text="Texture Transform Binds", icon="MATERIAL")

    (
        texture_transform_bind_collection_ops,
        texture_transform_bind_collection_item_ops,
        texture_transform_bind_index,
        texture_transform_bind,
        _,
    ) = draw_template_list(
        texture_transform_binds_box,
        VRM_UL_vrm1_texture_transform_bind.bl_idname,
        expression,
        "texture_transform_binds",
        "active_texture_transform_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_texture_transform_bind,
    )

    for texture_transform_bind_collection_op in texture_transform_bind_collection_ops:
        texture_transform_bind_collection_op.armature_name = armature.name
        texture_transform_bind_collection_op.expression_name = expression.name

    for (
        texture_transform_bind_collection_item_op
    ) in texture_transform_bind_collection_item_ops:
        texture_transform_bind_collection_item_op.bind_index = (
            texture_transform_bind_index
        )

    if isinstance(texture_transform_bind, Vrm1TextureTransformBindPropertyGroup):
        draw_vrm1_expressions_texture_transform_bind_layout(
            context,
            texture_transform_binds_box,
            texture_transform_bind,
        )


class VRM_PT_vrm1_expressions_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_expressions_armature_object_property"
    bl_label = "Expressions"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_expressions_layout(
            active_object,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.expressions,
        )


class VRM_PT_vrm1_expressions_ui(Panel):
    bl_idname = "VRM_PT_vrm1_expressions_ui"
    bl_label = "Expressions"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_expressions_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.expressions,
        )


def draw_vrm1_meta_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    meta: Vrm1MetaPropertyGroup,
) -> None:
    defer_migrate(armature.name)

    thumbnail_column = layout.column()
    thumbnail_column.label(text="Thumbnail:")
    thumbnail_column.template_ID_preview(meta, "thumbnail_image")

    layout.prop(meta, "vrm_name", icon="FILE_BLEND")
    layout.prop(meta, "version", icon="LINENUMBERS_ON")

    authors_column = layout.column()
    authors_column.label(text="Authors:")

    (
        author_collection_ops,
        author_collection_item_ops,
        author_index,
        _,
        _,
    ) = draw_template_list(
        authors_column,
        VRM_UL_vrm1_meta_author.bl_idname,
        meta,
        "authors",
        "active_author_index",
        vrm1_ops.VRM_OT_add_vrm1_meta_author,
        vrm1_ops.VRM_OT_remove_vrm1_meta_author,
        vrm1_ops.VRM_OT_move_up_vrm1_meta_author,
        vrm1_ops.VRM_OT_move_down_vrm1_meta_author,
        can_remove=lambda _: len(meta.authors) >= 2,
        compact=True,
    )

    for author_collection_op in author_collection_ops:
        author_collection_op.armature_name = armature.name

    for author_collection_item_op in author_collection_item_ops:
        author_collection_item_op.author_index = author_index

    layout.prop(meta, "copyright_information")
    layout.prop(meta, "contact_information")

    references_column = layout.column()
    references_column.label(text="References:")

    (
        reference_collection_ops,
        reference_collection_item_ops,
        reference_index,
        _,
        _,
    ) = draw_template_list(
        references_column,
        VRM_UL_vrm1_meta_reference.bl_idname,
        meta,
        "references",
        "active_reference_index",
        vrm1_ops.VRM_OT_add_vrm1_meta_reference,
        vrm1_ops.VRM_OT_remove_vrm1_meta_reference,
        vrm1_ops.VRM_OT_move_up_vrm1_meta_reference,
        vrm1_ops.VRM_OT_move_down_vrm1_meta_reference,
        compact=True,
    )

    for reference_collection_op in reference_collection_ops:
        reference_collection_op.armature_name = armature.name

    for reference_collection_item_op in reference_collection_item_ops:
        reference_collection_item_op.reference_index = reference_index

    layout.prop(meta, "third_party_licenses")
    # layout.prop(meta, "license_url", icon="URL")
    layout.prop(meta, "avatar_permission", icon="MATCLOTH")
    layout.prop(meta, "commercial_usage", icon="SOLO_OFF")
    layout.prop(meta, "credit_notation")
    layout.prop(meta, "modification")
    layout.prop(meta, "allow_excessively_violent_usage")
    layout.prop(meta, "allow_excessively_sexual_usage")
    layout.prop(meta, "allow_political_or_religious_usage")
    layout.prop(meta, "allow_antisocial_or_hate_usage")
    layout.prop(meta, "allow_redistribution")
    layout.prop(meta, "other_license_url", icon="URL")


class VRM_PT_vrm1_meta_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_meta_armature_object_property"
    bl_label = "Meta"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_vrm1_meta_layout(active_object, context, self.layout, ext.vrm1.meta)


class VRM_PT_vrm1_meta_ui(Panel):
    bl_idname = "VRM_PT_vrm1_meta_ui"
    bl_label = "Meta"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_meta_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.meta,
        )


class VRM_PT_vrm1_bone_property(Panel):
    bl_idname = "VRM_PT_vrm1_bone_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(cls, context: Context) -> bool:
        active_object = context.active_object
        if not active_object:
            return False
        if active_object.type != "ARMATURE":
            return False
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return False
        if not armature_data.bones.active:
            return False
        return search.current_armature_is_vrm1(context)

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        if active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        # context.active_bone is a EditBone
        bone = armature_data.bones.active
        if not bone:
            return
        ext = get_bone_extension(bone)
        layout = self.layout
        layout.prop(ext, "axis_translation")
