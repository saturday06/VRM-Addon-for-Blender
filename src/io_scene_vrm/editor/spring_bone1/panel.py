# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet
from typing import Optional

from bpy.types import Armature, Context, Object, Panel, UILayout

from .. import search
from ..extension import get_armature_extension
from ..migration import defer_migrate
from ..panel import VRM_PT_vrm_armature_object_property, draw_template_list
from ..search import active_object_is_vrm1_armature
from . import ops
from .property_group import (
    SpringBone1ColliderGroupPropertyGroup,
    SpringBone1ColliderPropertyGroup,
    SpringBone1JointPropertyGroup,
    SpringBone1SpringBonePropertyGroup,
    SpringBone1SpringPropertyGroup,
)
from .ui_list import (
    VRM_UL_spring_bone1_collider,
    VRM_UL_spring_bone1_collider_group,
    VRM_UL_spring_bone1_collider_group_collider,
    VRM_UL_spring_bone1_joint,
    VRM_UL_spring_bone1_spring,
    VRM_UL_spring_bone1_spring_collider_group,
)


def draw_spring_bone1_collider_sphere_layout(
    layout: UILayout,
    armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    layout.prop_search(collider.node, "bone_name", armature_data, "bones")
    layout.prop(collider, "ui_collider_type")
    if collider.bpy_object:
        layout.prop(collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Offset")
    layout.prop(collider.shape.sphere, "offset", text="")
    layout.separator(factor=0.5)
    layout.prop(collider.shape.sphere, "radius", slider=True)
    layout.prop(collider.extensions.vrmc_spring_bone_extended_collider, "enabled")


def draw_spring_bone1_collider_capsule_layout(
    layout: UILayout,
    armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    layout.prop_search(collider.node, "bone_name", armature_data, "bones")
    layout.prop(collider, "ui_collider_type")
    if collider.bpy_object:
        layout.prop(collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Head")
    layout.prop(collider.shape.capsule, "offset", text="")
    layout.separator(factor=0.5)
    layout.prop(collider.shape.capsule, "radius", slider=True)
    layout.separator(factor=0.5)
    if collider.bpy_object and collider.bpy_object.children:
        layout.prop(
            collider.bpy_object.children[0],
            "name",
            icon="MESH_UVSPHERE",
            text="Tail",
        )
    layout.prop(collider.shape.capsule, "tail", text="")
    layout.prop(collider.extensions.vrmc_spring_bone_extended_collider, "enabled")


def draw_spring_bone1_collider_extended_fallback_layout(
    layout: UILayout,
    _armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    extended = collider.extensions.vrmc_spring_bone_extended_collider
    layout.prop(extended, "automatic_fallback_generation")
    if extended.automatic_fallback_generation:
        return
    layout.prop(collider, "shape_type", text="Fallback")
    if collider.shape_type == collider.SHAPE_TYPE_SPHERE.identifier:
        layout.prop(collider.shape.sphere, "fallback_offset")
        layout.separator(factor=0.5)
        layout.prop(collider.shape.sphere, "fallback_radius", slider=True)
    elif collider.shape_type == collider.SHAPE_TYPE_CAPSULE.identifier:
        layout.prop(collider.shape.capsule, "fallback_offset")
        layout.separator(factor=0.5)
        layout.prop(collider.shape.capsule, "fallback_radius", slider=True)
        layout.separator(factor=0.5)
        layout.prop(collider.shape.capsule, "fallback_tail")


def draw_spring_bone1_collider_extended_sphere_layout(
    layout: UILayout,
    armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    extended = collider.extensions.vrmc_spring_bone_extended_collider
    layout.prop_search(collider.node, "bone_name", armature_data, "bones")
    layout.prop(collider, "ui_collider_type")
    if collider.bpy_object:
        layout.prop(collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Offset")
    layout.prop(extended.shape.sphere, "offset", text="")
    layout.separator(factor=0.5)
    layout.prop(extended.shape.sphere, "radius", slider=True)
    if not (extended.enabled and extended.shape.sphere.inside):
        layout.prop(extended, "enabled")
    draw_spring_bone1_collider_extended_fallback_layout(
        layout,
        armature_data,
        collider,
    )


def draw_spring_bone1_collider_extended_capsule_layout(
    layout: UILayout,
    armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    extended = collider.extensions.vrmc_spring_bone_extended_collider
    layout.prop_search(collider.node, "bone_name", armature_data, "bones")
    layout.prop(collider, "ui_collider_type")
    if collider.bpy_object:
        layout.prop(collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Head")
    layout.prop(extended.shape.capsule, "offset", text="")
    layout.separator(factor=0.5)
    layout.prop(extended.shape.capsule, "radius", slider=True)
    layout.separator(factor=0.5)
    if collider.bpy_object and collider.bpy_object.children:
        layout.prop(
            collider.bpy_object.children[0],
            "name",
            icon="MESH_UVSPHERE",
            text="Tail",
        )
    layout.prop(extended.shape.capsule, "tail", text="")
    if not (extended.enabled and extended.shape.capsule.inside):
        layout.prop(extended, "enabled")
    draw_spring_bone1_collider_extended_fallback_layout(
        layout,
        armature_data,
        collider,
    )


def draw_spring_bone1_collider_extended_plane_layout(
    layout: UILayout,
    armature_data: Armature,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    extended = collider.extensions.vrmc_spring_bone_extended_collider
    layout.prop_search(collider.node, "bone_name", armature_data, "bones")
    layout.prop(collider, "ui_collider_type")
    if collider.bpy_object:
        layout.prop(collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Offset")
    layout.prop(extended.shape.plane, "offset", text="")
    layout.separator(factor=0.5)
    layout.prop(extended.shape.plane, "normal")

    draw_spring_bone1_collider_extended_fallback_layout(
        layout,
        armature_data,
        collider,
    )


def draw_spring_bone1_collider_layout(
    armature: Object,
    layout: UILayout,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return
    extended = collider.extensions.vrmc_spring_bone_extended_collider
    if extended.enabled:
        if extended.shape_type == extended.SHAPE_TYPE_EXTENDED_PLANE.identifier:
            draw_spring_bone1_collider_extended_plane_layout(
                layout, armature_data, collider
            )
        elif extended.shape_type == extended.SHAPE_TYPE_EXTENDED_SPHERE.identifier:
            draw_spring_bone1_collider_extended_sphere_layout(
                layout, armature_data, collider
            )
        elif extended.shape_type == extended.SHAPE_TYPE_EXTENDED_CAPSULE.identifier:
            draw_spring_bone1_collider_extended_capsule_layout(
                layout, armature_data, collider
            )
    elif collider.shape_type == collider.SHAPE_TYPE_SPHERE.identifier:
        draw_spring_bone1_collider_sphere_layout(layout, armature_data, collider)
    elif collider.shape_type == collider.SHAPE_TYPE_CAPSULE.identifier:
        draw_spring_bone1_collider_capsule_layout(layout, armature_data, collider)
    layout.separator(factor=0.5)


def draw_spring_bone1_spring_bone_layout(
    armature: Object,
    layout: UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    defer_migrate(armature.name)

    layout.prop(spring_bone, "enable_animation")
    # layout.operator(ops.VRM_OT_reset_spring_bone1_animation_state.bl_idname)

    draw_spring_bone1_colliders_layout(armature, layout, spring_bone)
    draw_spring_bone1_collider_groups_layout(armature, layout, spring_bone)
    draw_spring_bone1_springs_layout(armature, layout, spring_bone)


def draw_spring_bone1_colliders_layout(
    armature: Object,
    layout: UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    colliders_box = layout.box()
    colliders_header_row = colliders_box.row()
    colliders_header_row.alignment = "LEFT"
    colliders_header_row.prop(
        spring_bone,
        "show_expanded_colliders",
        icon="TRIA_DOWN" if spring_bone.show_expanded_colliders else "TRIA_RIGHT",
        emboss=False,
    )

    if not spring_bone.show_expanded_colliders:
        return

    (
        collider_collection_ops,
        collider_collection_item_ops,
        collider_index,
        collider,
        _,
    ) = draw_template_list(
        colliders_box,
        VRM_UL_spring_bone1_collider.bl_idname,
        spring_bone,
        "colliders",
        "active_collider_index",
        ops.VRM_OT_add_spring_bone1_collider,
        ops.VRM_OT_remove_spring_bone1_collider,
        ops.VRM_OT_move_up_spring_bone1_collider,
        ops.VRM_OT_move_down_spring_bone1_collider,
    )

    for collider_collection_op in collider_collection_ops:
        collider_collection_op.armature_name = armature.name

    for collider_collection_item_op in collider_collection_item_ops:
        collider_collection_item_op.collider_index = collider_index

    if not isinstance(collider, SpringBone1ColliderPropertyGroup):
        return

    draw_spring_bone1_collider_layout(armature, colliders_box.column(), collider)


def draw_spring_bone1_collider_groups_layout(
    armature: Object,
    layout: UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    collider_groups_box = layout.box()
    collider_groups_header_row = collider_groups_box.row()
    collider_groups_header_row.alignment = "LEFT"
    collider_groups_header_row.prop(
        spring_bone,
        "show_expanded_collider_groups",
        icon="TRIA_DOWN" if spring_bone.show_expanded_collider_groups else "TRIA_RIGHT",
        emboss=False,
    )

    if not spring_bone.show_expanded_collider_groups:
        return

    (
        collider_group_collection_ops,
        collider_group_collection_item_ops,
        collider_group_index,
        collider_group,
        _,
    ) = draw_template_list(
        collider_groups_box,
        VRM_UL_spring_bone1_collider_group.bl_idname,
        spring_bone,
        "collider_groups",
        "active_collider_group_index",
        ops.VRM_OT_add_spring_bone1_collider_group,
        ops.VRM_OT_remove_spring_bone1_collider_group,
        ops.VRM_OT_move_up_spring_bone1_collider_group,
        ops.VRM_OT_move_down_spring_bone1_collider_group,
    )

    for collider_group_collection_op in collider_group_collection_ops:
        collider_group_collection_op.armature_name = armature.name

    for collider_group_collection_item_op in collider_group_collection_item_ops:
        collider_group_collection_item_op.collider_group_index = collider_group_index

    if not isinstance(collider_group, SpringBone1ColliderGroupPropertyGroup):
        return

    collider_group_column = collider_groups_box.column()
    collider_group_column.prop(
        collider_group,
        "vrm_name",
    )

    colliders_box = collider_group_column.box()
    colliders_column = colliders_box.column()
    colliders_column.label(text="Colliders:")

    (
        collider_collection_ops,
        collider_collection_item_ops,
        collider_index,
        _collider,
        _,
    ) = draw_template_list(
        colliders_column,
        VRM_UL_spring_bone1_collider_group_collider.bl_idname,
        collider_group,
        "colliders",
        "active_collider_index",
        ops.VRM_OT_add_spring_bone1_collider_group_collider,
        ops.VRM_OT_remove_spring_bone1_collider_group_collider,
        ops.VRM_OT_move_up_spring_bone1_collider_group_collider,
        ops.VRM_OT_move_down_spring_bone1_collider_group_collider,
    )

    for collider_collection_op in collider_collection_ops:
        collider_collection_op.armature_name = armature.name
        collider_collection_op.collider_group_index = collider_group_index

    for collider_collection_item_op in collider_collection_item_ops:
        collider_collection_item_op.collider_index = collider_index


def draw_spring_bone1_springs_layout(
    armature: Object,
    layout: UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    springs_box = layout.box()
    springs_header_row = springs_box.row()
    springs_header_row.alignment = "LEFT"
    springs_header_row.prop(
        spring_bone,
        "show_expanded_springs",
        icon="TRIA_DOWN" if spring_bone.show_expanded_springs else "TRIA_RIGHT",
        emboss=False,
    )

    if not spring_bone.show_expanded_springs:
        return

    (
        spring_collection_ops,
        spring_collection_item_ops,
        spring_index,
        spring,
        _,
    ) = draw_template_list(
        springs_box,
        VRM_UL_spring_bone1_spring.bl_idname,
        spring_bone,
        "springs",
        "active_spring_index",
        ops.VRM_OT_add_spring_bone1_spring,
        ops.VRM_OT_remove_spring_bone1_spring,
        ops.VRM_OT_move_up_spring_bone1_spring,
        ops.VRM_OT_move_down_spring_bone1_spring,
    )

    for spring_collection_op in spring_collection_ops:
        spring_collection_op.armature_name = armature.name

    for spring_collection_item_op in spring_collection_item_ops:
        spring_collection_item_op.spring_index = spring_index

    if not isinstance(spring, SpringBone1SpringPropertyGroup):
        return

    spring_column = springs_box.column()
    spring_column.prop(
        spring,
        "vrm_name",
    )
    spring_column.prop_search(
        spring.center,
        "bone_name",
        armature_data,
        "bones",
        text="Center",
    )

    joints_box = spring_column.box()
    joints_column = joints_box.column()
    joints_column.label(text="Joints:")

    (
        joint_collection_ops,
        joint_collection_item_ops,
        joint_index,
        joint,
        (add_joint_op, _, _, _),
    ) = draw_template_list(
        joints_column,
        VRM_UL_spring_bone1_joint.bl_idname,
        spring,
        "joints",
        "active_joint_index",
        ops.VRM_OT_add_spring_bone1_joint,
        ops.VRM_OT_remove_spring_bone1_joint,
        ops.VRM_OT_move_up_spring_bone1_joint,
        ops.VRM_OT_move_down_spring_bone1_joint,
    )

    for joint_collection_op in joint_collection_ops:
        joint_collection_op.armature_name = armature.name
        joint_collection_op.spring_index = spring_index

    for joint_collection_item_op in joint_collection_item_ops:
        joint_collection_item_op.joint_index = joint_index

    add_joint_op.guess_properties = True

    if isinstance(joint, SpringBone1JointPropertyGroup):
        joints_column.prop_search(joint.node, "bone_name", armature_data, "bones")
        joints_column.prop(joint, "stiffness", slider=True)
        joints_column.prop(joint, "gravity_power", slider=True)
        joints_column.prop(joint, "gravity_dir")
        joints_column.prop(joint, "drag_force", slider=True)
        joints_column.prop(joint, "hit_radius", slider=True)

    collider_groups_box = spring_column.box()
    collider_groups_column = collider_groups_box.column()
    collider_groups_column.label(text="Collider Groups:")

    (
        collider_group_collection_ops,
        collider_group_collection_item_ops,
        collider_group_index,
        _collider_group,
        _,
    ) = draw_template_list(
        collider_groups_column,
        VRM_UL_spring_bone1_spring_collider_group.bl_idname,
        spring,
        "collider_groups",
        "active_collider_group_index",
        ops.VRM_OT_add_spring_bone1_spring_collider_group,
        ops.VRM_OT_remove_spring_bone1_spring_collider_group,
        ops.VRM_OT_move_up_spring_bone1_spring_collider_group,
        ops.VRM_OT_move_down_spring_bone1_spring_collider_group,
    )

    for collider_group_collection_op in collider_group_collection_ops:
        collider_group_collection_op.armature_name = armature.name
        collider_group_collection_op.spring_index = spring_index

    for collider_group_collection_item_op in collider_group_collection_item_ops:
        collider_group_collection_item_op.collider_group_index = collider_group_index


class VRM_PT_spring_bone1_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm1_spring_bone_armature_object_property"
    bl_label = "Spring Bone"
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
        self.layout.label(icon="PHYSICS")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_spring_bone1_spring_bone_layout(
            active_object,
            self.layout,
            get_armature_extension(armature_data).spring_bone1,
        )


class VRM_PT_spring_bone1_ui(Panel):
    bl_idname = "VRM_PT_vrm1_spring_bone_ui"
    bl_label = "Spring Bone"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_spring_bone1_spring_bone_layout(
            armature,
            self.layout,
            get_armature_extension(armature_data).spring_bone1,
        )


class VRM_PT_spring_bone1_collider_property(Panel):
    bl_idname = "VRM_PT_spring_bone1_collider_property"
    bl_label = "VRM Spring Bone Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def active_armature_and_collider(
        cls, context: Context
    ) -> Optional[tuple[Object, SpringBone1ColliderPropertyGroup]]:
        active_object = context.active_object
        if not active_object:
            return None
        if active_object.type != "EMPTY":
            return None
        parent = active_object.parent
        if not parent:
            return None

        if active_object.parent_type == "BONE":
            collider_object = context.active_object
        elif active_object.parent_type == "OBJECT":
            if parent.type == "ARMATURE":
                collider_object = active_object
            elif parent.parent_type == "BONE" or (
                parent.parent_type == "OBJECT"
                and parent.parent
                and parent.parent.type == "ARMATURE"
            ):
                collider_object = parent
            else:
                return None
        else:
            return None
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            armature_data = obj.data
            if not isinstance(armature_data, Armature):
                continue
            for collider in get_armature_extension(
                armature_data
            ).spring_bone1.colliders:
                if collider.bpy_object == collider_object:
                    return (obj, collider)
        return None

    @classmethod
    def poll(cls, context: Context) -> bool:
        return cls.active_armature_and_collider(context) is not None

    def draw(self, context: Context) -> None:
        armature_and_collider = self.active_armature_and_collider(context)
        if armature_and_collider is None:
            return
        armature, collider = armature_and_collider
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        if get_armature_extension(armature_data).is_vrm1():
            draw_spring_bone1_collider_layout(armature, self.layout.column(), collider)
            return

        self.layout.label(text="This is a VRM 1.0 Spring Bone Collider", icon="INFO")
