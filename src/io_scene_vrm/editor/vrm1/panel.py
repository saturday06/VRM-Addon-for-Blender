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
from .menu import VRM_MT_vrm1_expression
from .ops import draw_bone_prop_search
from .property_group import (
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
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


def draw_vrm1_humanoid_required_bones_layout(
    armature: Object,
    layout: UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="Required VRM Human Bones", icon="ARMATURE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    label_column = row.column(align=True)
    label_column.label(text=HumanBoneSpecifications.HEAD.label)
    label_column.label(text=HumanBoneSpecifications.SPINE.label)
    label_column.label(text=HumanBoneSpecifications.HIPS.label)

    search_column = row.column(align=True)
    draw_bone_prop_search(search_column, HumanBoneSpecifications.HEAD, armature)
    draw_bone_prop_search(search_column, HumanBoneSpecifications.SPINE, armature)
    draw_bone_prop_search(search_column, HumanBoneSpecifications.HIPS, armature)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    label_column = row.column(align=True)
    label_column.label(text="")
    label_column.label(text=HumanBoneSpecifications.LEFT_UPPER_ARM.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.LEFT_LOWER_ARM.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.LEFT_HAND.label_no_left_right)
    label_column.separator()
    label_column.label(text=HumanBoneSpecifications.LEFT_UPPER_LEG.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.LEFT_LOWER_LEG.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.LEFT_FOOT.label_no_left_right)

    search_column = row.column(align=True)
    right_left_row = search_column.row(align=True)
    right_left_row.label(text="Right")
    right_left_row.label(text="Left")

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_UPPER_ARM, armature
    )
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_UPPER_ARM, armature
    )

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_LOWER_ARM, armature
    )
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_LOWER_ARM, armature
    )

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_HAND, armature)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_HAND, armature)

    search_column.separator()

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_UPPER_LEG, armature
    )
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_UPPER_LEG, armature
    )

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_LOWER_LEG, armature
    )
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_LOWER_LEG, armature
    )

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_FOOT, armature)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_FOOT, armature)


def draw_vrm1_humanoid_optional_bones_layout(
    armature: Object,
    layout: UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="Optional VRM Human Bones", icon="BONE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
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
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_EYE, armature)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_EYE, armature)

    draw_bone_prop_search(search_column, HumanBoneSpecifications.JAW, armature)
    draw_bone_prop_search(search_column, HumanBoneSpecifications.NECK, armature)

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_SHOULDER, armature
    )
    draw_bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_SHOULDER, armature
    )

    draw_bone_prop_search(search_column, HumanBoneSpecifications.UPPER_CHEST, armature)
    draw_bone_prop_search(search_column, HumanBoneSpecifications.CHEST, armature)

    right_left_row = search_column.row(align=True)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_TOES, armature)
    draw_bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_TOES, armature)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    label_column = row.column(align=True)
    label_column.label(text="", translate=False)
    label_column.label(text="Left Thumb:")
    label_column.label(text="Left Index:")
    label_column.label(text="Left Middle:")
    label_column.label(text="Left Ring:")
    label_column.label(text="Left Little:")
    label_column.separator()
    label_column.label(text="Right Thumb:")
    label_column.label(text="Right Index:")
    label_column.label(text="Right Middle:")
    label_column.label(text="Right Ring:")
    label_column.label(text="Right Little:")

    search_column = row.column(align=True)

    finger_row = search_column.row(align=True)
    finger_row.label(text="Root")
    finger_row.label(text="", translate=False)
    finger_row.label(text="Tip")

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_THUMB_METACARPAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_THUMB_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_THUMB_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_INDEX_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_INDEX_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_MIDDLE_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_RING_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_RING_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_RING_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.LEFT_LITTLE_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_THUMB_METACARPAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_THUMB_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_INDEX_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_RING_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_RING_DISTAL, armature
    )

    finger_row = search_column.row(align=True)
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE, armature
    )
    draw_bone_prop_search(
        finger_row, HumanBoneSpecifications.RIGHT_LITTLE_DISTAL, armature
    )


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
        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(context, data.name)

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
        pose_library = humanoid.pose_library
        if pose_library and pose_library.pose_markers:
            column.prop_search(
                humanoid,
                "pose_marker_name",
                pose_library,
                "pose_markers",
                text="Pose",
                translate=False,
            )

    bone_operator_column = layout.column()
    layout_operator(
        bone_operator_column,
        vrm1_ops.VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
        icon="ARMATURE_DATA",
    ).armature_object_name = armature.name

    if ops.VRM_OT_simplify_vroid_bones.vroid_bones_exist(data):
        simplify_vroid_bones_op = layout_operator(
            armature_box,
            ops.VRM_OT_simplify_vroid_bones,
            text=pgettext(ops.VRM_OT_simplify_vroid_bones.bl_label),
            icon="GREASEPENCIL",
        )
        simplify_vroid_bones_op.armature_object_name = armature.name

    draw_vrm1_humanoid_required_bones_layout(armature, armature_box.box())
    draw_vrm1_humanoid_optional_bones_layout(armature, armature_box.box())

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
        VRM_UL_vrm1_first_person_mesh_annotation,
        first_person,
        "mesh_annotations",
        "active_mesh_annotation_index",
        vrm1_ops.VRM_OT_add_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_remove_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_move_up_vrm1_first_person_mesh_annotation,
        vrm1_ops.VRM_OT_move_down_vrm1_first_person_mesh_annotation,
    )

    for mesh_annotation_collection_op in mesh_annotation_collection_ops:
        mesh_annotation_collection_op.armature_object_name = armature.name

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

        all_expression_names = list(expressions.all_name_to_expression_dict().keys())
        if (
            0
            <= expressions.active_expression_ui_list_element_index
            < len(all_expression_names)
        ):
            expression_name = all_expression_names[
                expressions.active_expression_ui_list_element_index
            ]
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
    refresh_op.armature_object_name = armature.name
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

    expression_preset_and_expressions = (
        expressions.preset.expression_preset_and_expressions()
    )

    (
        expression_collection_ops,
        expression_collection_item_ops,
        expression_ui_list_element_index,
        _,
        _,
    ) = draw_template_list(
        layout,
        VRM_UL_vrm1_expression,
        expressions,
        "expression_ui_list_elements",
        "active_expression_ui_list_element_index",
        vrm1_ops.VRM_OT_add_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_remove_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_move_up_vrm1_expressions_custom_expression,
        vrm1_ops.VRM_OT_move_down_vrm1_expressions_custom_expression,
        can_remove=lambda active_collection_index: (
            active_collection_index >= len(expression_preset_and_expressions)
        ),
        can_move=lambda active_collection_index: (
            len(expressions.custom) >= 2
            and active_collection_index >= len(expression_preset_and_expressions)
        ),
        menu_and_context_pointer_set_callback=(
            VRM_MT_vrm1_expression,
            VRM_MT_vrm1_expression.layout_context_pointer_set(armature),
        ),
    )

    for expression_collection_op in expression_collection_ops:
        expression_collection_op.armature_object_name = armature.name
        expression_collection_op.custom_expression_name = "custom"

    custom_index = expression_ui_list_element_index - len(
        expression_preset_and_expressions
    )

    if 0 <= expression_ui_list_element_index < len(expression_preset_and_expressions):
        expression_preset, expression = expression_preset_and_expressions[
            expression_ui_list_element_index
        ]
        layout.label(
            text=expression_preset.name, translate=False, icon=expression_preset.icon
        )
        expression_name = expression_preset.name
    elif 0 <= custom_index < len(expressions.custom):
        expression = expressions.custom[custom_index]

        for expression_collection_item_op in expression_collection_item_ops:
            expression_collection_item_op.custom_expression_name = (
                expression.custom_name
            )

        layout.prop(expression, "custom_name")
        expression_name = expression.custom_name
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
        VRM_UL_vrm1_morph_target_bind,
        expression,
        "morph_target_binds",
        "active_morph_target_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_morph_target_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_morph_target_bind,
    )

    for morph_target_bind_collection_op in morph_target_bind_collection_ops:
        morph_target_bind_collection_op.armature_object_name = armature.name
        morph_target_bind_collection_op.expression_name = expression_name

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
        VRM_UL_vrm1_material_color_bind,
        expression,
        "material_color_binds",
        "active_material_color_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_material_color_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_material_color_bind,
    )

    for material_color_bind_collection_op in material_color_bind_collection_ops:
        material_color_bind_collection_op.armature_object_name = armature.name
        material_color_bind_collection_op.expression_name = expression_name

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
        VRM_UL_vrm1_texture_transform_bind,
        expression,
        "texture_transform_binds",
        "active_texture_transform_bind_index",
        vrm1_ops.VRM_OT_add_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_remove_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_move_up_vrm1_expression_texture_transform_bind,
        vrm1_ops.VRM_OT_move_down_vrm1_expression_texture_transform_bind,
    )

    for texture_transform_bind_collection_op in texture_transform_bind_collection_ops:
        texture_transform_bind_collection_op.armature_object_name = armature.name
        texture_transform_bind_collection_op.expression_name = expression_name

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
        VRM_UL_vrm1_meta_author,
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
        author_collection_op.armature_object_name = armature.name

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
        VRM_UL_vrm1_meta_reference,
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
        reference_collection_op.armature_object_name = armature.name

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
