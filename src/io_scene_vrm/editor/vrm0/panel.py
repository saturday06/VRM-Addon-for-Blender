# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet

import bpy
from bpy.app.translations import pgettext
from bpy.types import (
    Armature,
    Context,
    Mesh,
    Object,
    Panel,
    UILayout,
)

from ...common.vrm0.human_bone import HumanBoneSpecification, HumanBoneSpecifications
from .. import ops, search
from ..extension import (
    get_armature_extension,
    get_material_extension,
    get_scene_extension,
)
from ..migration import defer_migrate
from ..ops import layout_operator
from ..panel import VRM_PT_vrm_armature_object_property, draw_template_list
from ..search import active_object_is_vrm0_armature
from . import ops as vrm0_ops
from .property_group import (
    Vrm0BlendShapeBindPropertyGroup,
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0BlendShapeMasterPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
    Vrm0SecondaryAnimationPropertyGroup,
)
from .ui_list import (
    VRM_UL_vrm0_blend_shape_bind,
    VRM_UL_vrm0_blend_shape_group,
    VRM_UL_vrm0_first_person_mesh_annotation,
    VRM_UL_vrm0_material_value_bind,
    VRM_UL_vrm0_secondary_animation_collider_group,
    VRM_UL_vrm0_secondary_animation_collider_group_collider,
    VRM_UL_vrm0_secondary_animation_group,
    VRM_UL_vrm0_secondary_animation_group_bone,
    VRM_UL_vrm0_secondary_animation_group_collider_group,
)


def bone_prop_search(
    layout: UILayout,
    human_bone_specification: HumanBoneSpecification,
    icon: str,
    humanoid: Vrm0HumanoidPropertyGroup,
) -> None:
    props = None
    for human_bone in humanoid.human_bones:
        if human_bone.bone == human_bone_specification.name.value:
            props = human_bone
            break
    if not props:
        return

    layout.prop_search(
        props.node,
        "bone_name",
        props,
        "node_candidates",
        text="",
        translate=False,
        icon=icon,
    )


def draw_vrm0_humanoid_operators_layout(
    armature: Object,
    layout: UILayout,
) -> None:
    bone_operator_column = layout.column()
    layout_operator(
        bone_operator_column,
        vrm0_ops.VRM_OT_assign_vrm0_humanoid_human_bones_automatically,
        icon="ARMATURE_DATA",
    ).armature_name = armature.name
    save_load_row = bone_operator_column.split(factor=0.5, align=True)
    save_load_row.operator(
        ops.VRM_OT_save_human_bone_mappings.bl_idname,
        icon="EXPORT",
        text="Save",
    )
    save_load_row.operator(
        ops.VRM_OT_load_human_bone_mappings.bl_idname, icon="IMPORT", text="Load"
    )


def draw_vrm0_humanoid_required_bones_layout(
    armature: Object,
    layout: UILayout,
    split_factor: float = 0.2,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    humanoid = get_armature_extension(armature_data).vrm0.humanoid
    layout.label(text="VRM Required Bones", icon="ARMATURE_DATA")
    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text=HumanBoneSpecifications.HEAD.label)
    column.label(text=HumanBoneSpecifications.NECK.label)
    column.label(text=HumanBoneSpecifications.CHEST.label)
    column.label(text=HumanBoneSpecifications.SPINE.label)
    column.label(text=HumanBoneSpecifications.HIPS.label)
    column = row.column(align=True)
    icon = "USER"
    bone_prop_search(column, HumanBoneSpecifications.HEAD, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.NECK, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.CHEST, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.SPINE, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.HIPS, icon, humanoid)

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
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_UPPER_ARM, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_LOWER_ARM, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_HAND, icon, humanoid)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_UPPER_LEG, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_LOWER_LEG, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_FOOT, icon, humanoid)

    column = row.column(align=True)
    column.label(text="Left")
    icon = "VIEW_PAN"
    bone_prop_search(column, HumanBoneSpecifications.LEFT_UPPER_ARM, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_LOWER_ARM, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_HAND, icon, humanoid)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBoneSpecifications.LEFT_UPPER_LEG, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_LOWER_LEG, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_FOOT, icon, humanoid)


def draw_vrm0_humanoid_optional_bones_layout(
    armature: Object,
    layout: UILayout,
    split_factor: float = 0.2,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    humanoid = get_armature_extension(armature_data).vrm0.humanoid
    split_factor = 0.2

    layout.label(text="VRM Optional Bones", icon="BONE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    icon = "HIDE_OFF"
    label_column = row.column(align=True)
    label_column.label(text="")
    label_column.label(text=HumanBoneSpecifications.LEFT_EYE.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.JAW.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_SHOULDER.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.UPPER_CHEST.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_TOES.label_no_left_right)

    search_column = row.column(align=True)

    right_left_row = search_column.row(align=True)
    right_left_row.label(text="Right")
    right_left_row.label(text="Left")

    right_left_row = search_column.row(align=True)
    bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_EYE, icon, humanoid)
    bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_EYE, icon, humanoid)

    icon = "USER"
    bone_prop_search(search_column, HumanBoneSpecifications.JAW, icon, humanoid)

    icon = "VIEW_PAN"
    right_left_row = search_column.row(align=True)
    bone_prop_search(
        right_left_row, HumanBoneSpecifications.RIGHT_SHOULDER, icon, humanoid
    )
    bone_prop_search(
        right_left_row, HumanBoneSpecifications.LEFT_SHOULDER, icon, humanoid
    )

    icon = "USER"
    bone_prop_search(search_column, HumanBoneSpecifications.UPPER_CHEST, icon, humanoid)

    icon = "MOD_DYNAMICPAINT"
    right_left_row = search_column.row(align=True)
    bone_prop_search(right_left_row, HumanBoneSpecifications.RIGHT_TOES, icon, humanoid)
    bone_prop_search(right_left_row, HumanBoneSpecifications.LEFT_TOES, icon, humanoid)

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
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_THUMB_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_INDEX_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL, icon, humanoid
    )
    bone_prop_search(column, HumanBoneSpecifications.LEFT_RING_PROXIMAL, icon, humanoid)
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL, icon, humanoid
    )
    column.separator()
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_RING_PROXIMAL, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL, icon, humanoid
    )

    column = row.column(align=True)
    column.label(text="", translate=False)
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_THUMB_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_RING_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE, icon, humanoid
    )
    column.separator()
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_THUMB_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE, icon, humanoid
    )
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE, icon, humanoid
    )

    column = row.column(align=True)
    column.label(text="Tip")
    bone_prop_search(column, HumanBoneSpecifications.LEFT_THUMB_DISTAL, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_INDEX_DISTAL, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_MIDDLE_DISTAL, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_RING_DISTAL, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.LEFT_LITTLE_DISTAL, icon, humanoid)
    column.separator()
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_THUMB_DISTAL, icon, humanoid)
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_INDEX_DISTAL, icon, humanoid)
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL, icon, humanoid
    )
    bone_prop_search(column, HumanBoneSpecifications.RIGHT_RING_DISTAL, icon, humanoid)
    bone_prop_search(
        column, HumanBoneSpecifications.RIGHT_LITTLE_DISTAL, icon, humanoid
    )


def draw_vrm0_humanoid_layout(
    context: Context,
    armature: Object,
    layout: UILayout,
    humanoid: Vrm0HumanoidPropertyGroup,
) -> None:
    if defer_migrate(armature.name):
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        Vrm0HumanoidPropertyGroup.defer_update_all_node_candidates(armature_data.name)

    data = armature.data
    if not isinstance(data, Armature):
        return

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

    draw_vrm0_humanoid_operators_layout(armature, armature_box)

    if ops.VRM_OT_simplify_vroid_bones.vroid_bones_exist(data):
        simplify_vroid_bones_op = layout_operator(
            armature_box,
            ops.VRM_OT_simplify_vroid_bones,
            text=pgettext(ops.VRM_OT_simplify_vroid_bones.bl_label),
            icon="GREASEPENCIL",
        )
        simplify_vroid_bones_op.armature_name = armature.name

    split_factor = 0.2
    draw_vrm0_humanoid_required_bones_layout(armature, armature_box.box(), split_factor)
    draw_vrm0_humanoid_optional_bones_layout(armature, armature_box.box(), split_factor)

    layout.label(text="Arm", icon="VIEW_PAN", translate=False)  # TODO: 翻訳
    layout.prop(
        humanoid,
        "arm_stretch",
    )
    layout.prop(humanoid, "upper_arm_twist")
    layout.prop(humanoid, "lower_arm_twist")
    layout.separator()
    layout.label(text="Leg", icon="MOD_DYNAMICPAINT")
    layout.prop(humanoid, "leg_stretch")
    layout.prop(humanoid, "upper_leg_twist")
    layout.prop(humanoid, "lower_leg_twist")
    layout.prop(humanoid, "feet_spacing")
    layout.separator()
    layout.prop(humanoid, "has_translation_dof")


class VRM_PT_vrm0_humanoid_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_humanoid_armature_object_property"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm0_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_humanoid_layout(
            context,
            active_object,
            self.layout,
            get_armature_extension(armature_data).vrm0.humanoid,
        )


class VRM_PT_vrm0_humanoid_ui(Panel):
    bl_idname = "VRM_PT_vrm0_humanoid_ui"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm0(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="USER")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_humanoid_layout(
            context,
            armature,
            self.layout,
            get_armature_extension(armature_data).vrm0.humanoid,
        )


def draw_vrm0_first_person_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    first_person: Vrm0FirstPersonPropertyGroup,
) -> None:
    defer_migrate(armature.name)
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return
    layout.prop_search(
        first_person.first_person_bone, "bone_name", armature_data, "bones"
    )
    layout.prop(first_person, "first_person_bone_offset", icon="BONE_DATA")
    layout.prop(first_person, "look_at_type_name")
    layout.label(text="Mesh Annotations", icon="RESTRICT_RENDER_OFF")

    (
        mesh_annotation_collection_ops,
        mesh_annotation_collection_item_ops,
        mesh_annotation_index,
        _,
        _,
    ) = draw_template_list(
        layout,
        VRM_UL_vrm0_first_person_mesh_annotation.bl_idname,
        first_person,
        "mesh_annotations",
        "active_mesh_annotation_index",
        vrm0_ops.VRM_OT_add_vrm0_first_person_mesh_annotation,
        vrm0_ops.VRM_OT_remove_vrm0_first_person_mesh_annotation,
        vrm0_ops.VRM_OT_move_up_vrm0_first_person_mesh_annotation,
        vrm0_ops.VRM_OT_move_down_vrm0_first_person_mesh_annotation,
    )

    for mesh_annotation_collection_op in mesh_annotation_collection_ops:
        mesh_annotation_collection_op.armature_name = armature.name

    for mesh_annotation_collection_item_op in mesh_annotation_collection_item_ops:
        mesh_annotation_collection_item_op.mesh_annotation_index = mesh_annotation_index

    layout.separator()
    box = layout.box()
    box.label(text="Look At Horizontal Inner", icon="FULLSCREEN_EXIT")
    box.prop(first_person.look_at_horizontal_inner, "curve")
    box.prop(first_person.look_at_horizontal_inner, "x_range")
    box.prop(first_person.look_at_horizontal_inner, "y_range")
    box = layout.box()
    box.label(text="Look At Horizontal Outer", icon="FULLSCREEN_ENTER")
    box.prop(first_person.look_at_horizontal_outer, "curve")
    box.prop(first_person.look_at_horizontal_outer, "x_range")
    box.prop(first_person.look_at_horizontal_outer, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Up", icon="TRIA_UP")
    box.prop(first_person.look_at_vertical_up, "curve")
    box.prop(first_person.look_at_vertical_up, "x_range")
    box.prop(first_person.look_at_vertical_up, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Down", icon="TRIA_DOWN")
    box.prop(first_person.look_at_vertical_down, "curve")
    box.prop(first_person.look_at_vertical_down, "x_range")
    box.prop(first_person.look_at_vertical_down, "y_range")


class VRM_PT_vrm0_first_person_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_first_person_armature_object_property"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm0_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_vrm0_first_person_layout(
            active_object,
            context,
            self.layout,
            ext.vrm0.first_person,
        )


class VRM_PT_vrm0_first_person_ui(Panel):
    bl_idname = "VRM_PT_vrm0_first_person_ui"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm0(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_first_person_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm0.first_person,
        )


def draw_vrm0_blend_shape_master_layout(
    armature: Object,
    context: Context,
    layout: UILayout,
    blend_shape_master: Vrm0BlendShapeMasterPropertyGroup,
) -> None:
    defer_migrate(armature.name)
    blend_data = context.blend_data

    (
        blend_shape_group_collection_ops,
        blend_shape_group_collection_item_ops,
        blend_shape_group_index,
        blend_shape_group,
        (add_blend_shape_group_op, _, _, _),
    ) = draw_template_list(
        layout,
        VRM_UL_vrm0_blend_shape_group.bl_idname,
        blend_shape_master,
        "blend_shape_groups",
        "active_blend_shape_group_index",
        vrm0_ops.VRM_OT_add_vrm0_blend_shape_group,
        vrm0_ops.VRM_OT_remove_vrm0_blend_shape_group,
        vrm0_ops.VRM_OT_move_up_vrm0_blend_shape_group,
        vrm0_ops.VRM_OT_move_down_vrm0_blend_shape_group,
    )

    for blend_shape_group_collection_op in blend_shape_group_collection_ops:
        blend_shape_group_collection_op.armature_name = armature.name

    for blend_shape_group_collection_item_op in blend_shape_group_collection_item_ops:
        blend_shape_group_collection_item_op.blend_shape_group_index = (
            blend_shape_group_index
        )

    add_blend_shape_group_op.name = "New"

    if isinstance(blend_shape_group, Vrm0BlendShapeGroupPropertyGroup):
        column = layout.column()
        column.prop(blend_shape_group, "name")
        column.prop(blend_shape_group, "preset_name")
        column.prop(blend_shape_group, "is_binary", icon="IPO_CONSTANT")
        column.prop(blend_shape_group, "preview", icon="PLAY", text="Preview")
        column.separator(factor=0.5)

        binds_box = column.box()
        binds_box.label(text="Binds", icon="MESH_DATA")

        (
            bind_collection_ops,
            bind_collection_item_ops,
            bind_index,
            bind,
            _,
        ) = draw_template_list(
            binds_box,
            VRM_UL_vrm0_blend_shape_bind.bl_idname,
            blend_shape_group,
            "binds",
            "active_bind_index",
            vrm0_ops.VRM_OT_add_vrm0_blend_shape_bind,
            vrm0_ops.VRM_OT_remove_vrm0_blend_shape_bind,
            vrm0_ops.VRM_OT_move_up_vrm0_blend_shape_bind,
            vrm0_ops.VRM_OT_move_down_vrm0_blend_shape_bind,
        )

        for bind_collection_op in bind_collection_ops:
            bind_collection_op.armature_name = armature.name
            bind_collection_op.blend_shape_group_index = blend_shape_group_index

        for bind_collection_item_op in bind_collection_item_ops:
            bind_collection_item_op.bind_index = bind_index

        if isinstance(bind, Vrm0BlendShapeBindPropertyGroup):
            bind_column = binds_box.column()
            bind_column.prop(
                bind.mesh,
                "bpy_object",
                text="Mesh",
                icon="OUTLINER_OB_MESH",
            )

            mesh_object = blend_data.objects.get(bind.mesh.mesh_object_name)
            if mesh_object:
                mesh_data = mesh_object.data
                if isinstance(mesh_data, Mesh):
                    shape_keys = mesh_data.shape_keys
                    if shape_keys:
                        bind_column.prop_search(
                            bind,
                            "index",
                            shape_keys,
                            "key_blocks",
                            text="Shape key",
                        )
            bind_column.prop(bind, "weight", slider=True)

        column.separator(factor=0.2)
        material_value_binds_box = column.box()
        material_value_binds_box.label(text="Material Values", icon="MATERIAL")

        (
            material_value_collection_ops,
            material_value_collection_item_ops,
            material_value_index,
            material_value,
            _,
        ) = draw_template_list(
            material_value_binds_box,
            VRM_UL_vrm0_material_value_bind.bl_idname,
            blend_shape_group,
            "material_values",
            "active_material_value_index",
            vrm0_ops.VRM_OT_add_vrm0_material_value_bind,
            vrm0_ops.VRM_OT_remove_vrm0_material_value_bind,
            vrm0_ops.VRM_OT_move_up_vrm0_material_value_bind,
            vrm0_ops.VRM_OT_move_down_vrm0_material_value_bind,
        )

        for material_value_bind_collection_op in material_value_collection_ops:
            material_value_bind_collection_op.armature_name = armature.name
            material_value_bind_collection_op.blend_shape_group_index = (
                blend_shape_group_index
            )

        for (
            material_value_bind_collection_item_op
        ) in material_value_collection_item_ops:
            material_value_bind_collection_item_op.material_value_index = (
                material_value_index
            )

        if isinstance(material_value, Vrm0MaterialValueBindPropertyGroup):
            material_value_column = material_value_binds_box.column()
            material_value_column.prop_search(
                material_value, "material", blend_data, "materials"
            )

            if not material_value.material:
                material_value_column.prop(
                    material_value, "property_name", icon="PROPERTIES"
                )
            else:
                scene_extension = get_scene_extension(context.scene)
                scene_extension.defer_update_vrm0_material_property_names()
                material = material_value.material
                ext = get_material_extension(material)
                node, legacy_shader_name = search.legacy_shader_node(material)
                if ext.mtoon1.enabled or (
                    node and legacy_shader_name == "MToon_unversioned"
                ):
                    if bpy.app.version >= (3, 2):
                        material_value_column.prop_search(
                            material_value,
                            "property_name",
                            get_scene_extension(context.scene),
                            "vrm0_material_mtoon0_property_names",
                            icon="PROPERTIES",
                            results_are_suggestions=True,
                        )
                    else:
                        material_value_column.prop_search(
                            material_value,
                            "property_name",
                            get_scene_extension(context.scene),
                            "vrm0_material_mtoon0_property_names",
                            icon="PROPERTIES",
                        )
                elif bpy.app.version >= (3, 2):
                    material_value_column.prop_search(
                        material_value,
                        "property_name",
                        get_scene_extension(context.scene),
                        "vrm0_material_gltf_property_names",
                        icon="PROPERTIES",
                        results_are_suggestions=True,
                    )
                else:
                    material_value_column.prop_search(
                        material_value,
                        "property_name",
                        get_scene_extension(context.scene),
                        "vrm0_material_gltf_property_names",
                        icon="PROPERTIES",
                    )

            for (
                target_value_index,
                target_value,
            ) in enumerate(material_value.target_value):
                target_value_row = material_value_column.row()
                target_value_row.prop(
                    target_value, "value", text=f"Value {target_value_index}"
                )
                remove_target_value_op = layout_operator(
                    target_value_row,
                    vrm0_ops.VRM_OT_remove_vrm0_material_value_bind_target_value,
                    text="",
                    icon="REMOVE",
                )
                remove_target_value_op.armature_name = armature.name
                remove_target_value_op.blend_shape_group_index = blend_shape_group_index
                remove_target_value_op.material_value_index = material_value_index
                remove_target_value_op.target_value_index = target_value_index
            add_target_value_op = layout_operator(
                material_value_column,
                vrm0_ops.VRM_OT_add_vrm0_material_value_bind_target_value,
                icon="ADD",
            )
            add_target_value_op.armature_name = armature.name
            add_target_value_op.blend_shape_group_index = blend_shape_group_index
            add_target_value_op.material_value_index = material_value_index


class VRM_PT_vrm0_blend_shape_master_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_blend_shape_master_armature_object_property"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm0_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_vrm0_blend_shape_master_layout(
            active_object, context, self.layout, ext.vrm0.blend_shape_master
        )


class VRM_PT_vrm0_blend_shape_master_ui(Panel):
    bl_idname = "VRM_PT_vrm0_blend_shape_master_ui"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm0(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_blend_shape_master_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm0.blend_shape_master,
        )


def draw_vrm0_secondary_animation_layout(
    armature: Object,
    layout: UILayout,
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
) -> None:
    defer_migrate(armature.name)
    draw_vrm0_secondary_animation_bone_groups_layout(
        armature, layout, secondary_animation
    )
    draw_vrm0_secondary_animation_collider_groups_layout(
        armature, layout, secondary_animation
    )


def draw_vrm0_secondary_animation_bone_groups_layout(
    armature: Object,
    layout: UILayout,
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
) -> None:
    data = armature.data
    if not isinstance(data, Armature):
        return

    header_row = layout.row()
    header_row.alignment = "LEFT"
    header_row.prop(
        secondary_animation,
        "show_expanded_bone_groups",
        icon="TRIA_DOWN"
        if secondary_animation.show_expanded_bone_groups
        else "TRIA_RIGHT",
        emboss=False,
    )
    if not secondary_animation.show_expanded_bone_groups:
        return

    box = layout.box()

    (
        bone_group_collection_ops,
        bone_group_collection_item_ops,
        bone_group_index,
        bone_group,
        _,
    ) = draw_template_list(
        box,
        VRM_UL_vrm0_secondary_animation_group.bl_idname,
        secondary_animation,
        "bone_groups",
        "active_bone_group_index",
        vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group,
        vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group,
        vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group,
        vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group,
    )

    for bone_group_collection_op in bone_group_collection_ops:
        bone_group_collection_op.armature_name = armature.name

    for bone_group_collection_item_op in bone_group_collection_item_ops:
        bone_group_collection_item_op.bone_group_index = bone_group_index

    if not isinstance(bone_group, Vrm0SecondaryAnimationGroupPropertyGroup):
        return

    column = box.column()
    column.prop(bone_group, "comment", icon="BOOKMARKS")
    column.prop(bone_group, "stiffiness", icon="RIGID_BODY_CONSTRAINT")
    column.prop(bone_group, "drag_force", icon="FORCE_DRAG")
    column.separator()
    column.prop(bone_group, "gravity_power", icon="OUTLINER_OB_FORCE_FIELD")
    column.prop(bone_group, "gravity_dir", icon="OUTLINER_OB_FORCE_FIELD")
    column.separator()
    column.prop_search(
        bone_group.center,
        "bone_name",
        data,
        "bones",
        icon="PIVOT_MEDIAN",
        text="Center Bone",
    )
    column.prop(
        bone_group,
        "hit_radius",
        icon="MOD_PHYSICS",
    )
    column.separator()

    column.label(text="Bones:")

    (
        bone_collection_ops,
        bone_collection_item_ops,
        bone_index,
        _bone,
        _,
    ) = draw_template_list(
        column,
        VRM_UL_vrm0_secondary_animation_group_bone.bl_idname,
        bone_group,
        "bones",
        "active_bone_index",
        vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_bone,
        vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_bone,
        vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group_bone,
        vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group_bone,
    )

    for bone_collection_op in bone_collection_ops:
        bone_collection_op.armature_name = armature.name
        bone_collection_op.bone_group_index = bone_group_index

    for bone_collection_item_op in bone_collection_item_ops:
        bone_collection_item_op.bone_index = bone_index

    column.separator()
    column.label(text="Collider Groups:")

    (
        collider_group_collection_ops,
        collider_group_collection_item_ops,
        collider_group_index,
        _collider_group,
        _,
    ) = draw_template_list(
        column,
        VRM_UL_vrm0_secondary_animation_group_collider_group.bl_idname,
        bone_group,
        "collider_groups",
        "active_collider_group_index",
        vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_collider_group,
        vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_collider_group,
        vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group_collider_group,
        vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group_collider_group,
    )

    for collider_group_collection_op in collider_group_collection_ops:
        collider_group_collection_op.armature_name = armature.name
        collider_group_collection_op.bone_group_index = bone_group_index

    for collider_group_collection_item_op in collider_group_collection_item_ops:
        collider_group_collection_item_op.collider_group_index = collider_group_index


def draw_vrm0_secondary_animation_collider_groups_layout(
    armature: Object,
    layout: UILayout,
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
) -> None:
    data = armature.data
    if not isinstance(data, Armature):
        return

    header_row = layout.row()
    header_row.alignment = "LEFT"
    header_row.prop(
        secondary_animation,
        "show_expanded_collider_groups",
        icon="TRIA_DOWN"
        if secondary_animation.show_expanded_collider_groups
        else "TRIA_RIGHT",
        emboss=False,
    )
    if not secondary_animation.show_expanded_collider_groups:
        return

    box = layout.box()

    (
        collider_group_collection_ops,
        collider_group_collection_item_ops,
        collider_group_index,
        collider_group,
        _,
    ) = draw_template_list(
        box,
        VRM_UL_vrm0_secondary_animation_collider_group.bl_idname,
        secondary_animation,
        "collider_groups",
        "active_collider_group_index",
        vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group,
        vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group,
        vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_collider_group,
        vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_collider_group,
    )

    for collider_group_collection_op in collider_group_collection_ops:
        collider_group_collection_op.armature_name = armature.name

    for collider_group_collection_item_op in collider_group_collection_item_ops:
        collider_group_collection_item_op.collider_group_index = collider_group_index

    if not isinstance(collider_group, Vrm0SecondaryAnimationColliderGroupPropertyGroup):
        return

    column = box.column()
    column.label(text=collider_group.name)
    column.prop_search(collider_group.node, "bone_name", data, "bones")
    column.label(text="Colliders:")

    (
        collider_collection_ops,
        collider_collection_item_ops,
        collider_index,
        _,
        _,
    ) = draw_template_list(
        column,
        VRM_UL_vrm0_secondary_animation_collider_group_collider.bl_idname,
        collider_group,
        "colliders",
        "active_collider_index",
        vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group_collider,
        vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group_collider,
        vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_collider_group_collider,
        vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_collider_group_collider,
    )

    for collider_collection_op in collider_collection_ops:
        collider_collection_op.armature_name = armature.name
        collider_collection_op.collider_group_index = collider_group_index

    for collider_collection_item_op in collider_collection_item_ops:
        collider_collection_item_op.armature_name = armature.name
        collider_collection_item_op.collider_group_index = collider_group_index
        collider_collection_item_op.collider_index = collider_index


class VRM_PT_vrm0_secondary_animation_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_secondary_animation_armature_object_property"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm0_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_vrm0_secondary_animation_layout(
            active_object, self.layout, ext.vrm0.secondary_animation
        )


class VRM_PT_vrm0_secondary_animation_ui(Panel):
    bl_idname = "VRM_PT_vrm0_secondary_animation_ui"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm0(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_secondary_animation_layout(
            armature,
            self.layout,
            get_armature_extension(armature_data).vrm0.secondary_animation,
        )


def draw_vrm0_meta_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    meta: Vrm0MetaPropertyGroup,
) -> None:
    defer_migrate(armature.name)

    thumbnail_column = layout.column()
    thumbnail_column.label(text="Thumbnail:")
    thumbnail_column.template_ID_preview(meta, "texture")

    layout.prop(meta, "title", icon="FILE_BLEND")
    layout.prop(meta, "version", icon="LINENUMBERS_ON")
    layout.prop(meta, "author", icon="USER")
    layout.prop(meta, "contact_information", icon="URL")
    layout.prop(meta, "reference", icon="URL")
    layout.prop(meta, "allowed_user_name", icon="MATCLOTH")
    layout.prop(
        meta,
        "violent_ussage_name",
        icon="ORPHAN_DATA",
    )
    layout.prop(meta, "sexual_ussage_name", icon="HEART")
    layout.prop(
        meta,
        "commercial_ussage_name",
        icon="SOLO_OFF",
    )
    layout.prop(meta, "other_permission_url", icon="URL")
    layout.prop(meta, "license_name", icon="COMMUNITY")
    if meta.license_name == Vrm0MetaPropertyGroup.LICENSE_NAME_OTHER.identifier:
        layout.prop(meta, "other_license_url", icon="URL")


class VRM_PT_vrm0_meta_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_meta_armature_object_property"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_vrm0_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_vrm0_meta_layout(active_object, context, self.layout, ext.vrm0.meta)


class VRM_PT_vrm0_meta_ui(Panel):
    bl_idname = "VRM_PT_vrm0_meta_ui"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm0(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm0_meta_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm0.meta,
        )
