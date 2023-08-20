from typing import Optional

import bpy

from .. import search
from ..migration import migrate
from ..ops import layout_operator
from ..panel import VRM_PT_vrm_armature_object_property
from ..search import active_object_is_vrm1_armature
from . import ops
from .property_group import (
    SpringBone1ColliderPropertyGroup,
    SpringBone1SpringBonePropertyGroup,
)


def draw_spring_bone1_collider_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    collider: SpringBone1ColliderPropertyGroup,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, bpy.types.Armature):
        return
    if collider.shape_type == collider.SHAPE_TYPE_SPHERE:
        layout.prop_search(collider.node, "bone_name", armature_data, "bones")
        layout.prop(collider, "shape_type")
        if collider.bpy_object:
            layout.prop(
                collider.bpy_object, "name", icon="MESH_UVSPHERE", text="Offset"
            )
        layout.prop(collider.shape.sphere, "offset", text="")
        layout.separator(factor=0.5)
        layout.prop(collider.shape.sphere, "radius", slider=True)
    elif collider.shape_type == collider.SHAPE_TYPE_CAPSULE:
        layout.prop_search(collider.node, "bone_name", armature_data, "bones")
        layout.prop(collider, "shape_type")
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
    layout.separator(factor=0.5)


def draw_spring_bone1_spring_bone_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    armature_data = armature.data
    if not isinstance(armature_data, bpy.types.Armature):
        return

    layout.prop(spring_bone, "enable_animation")
    # layout.operator(ops.VRM_OT_reset_spring_bone1_animation_state.bl_idname)

    colliders_box = layout.box()
    colliders_row = colliders_box.row()
    colliders_row.alignment = "LEFT"
    colliders_row.prop(
        spring_bone,
        "show_expanded_colliders",
        icon="TRIA_DOWN" if spring_bone.show_expanded_colliders else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone.show_expanded_colliders:
        if spring_bone.colliders:
            colliders_expanded_box = colliders_box.box().column()
            for collider_index, collider in enumerate(spring_bone.colliders):
                if not collider.bpy_object:  # TODO: restore
                    continue

                collider_row = colliders_expanded_box.row()
                collider_row.alignment = "LEFT"
                collider_row.prop(
                    collider,
                    "show_expanded",
                    icon="TRIA_DOWN" if collider.show_expanded else "TRIA_RIGHT",
                    emboss=False,
                    text=collider.bpy_object.name,
                    translate=False,
                )

                if not collider.show_expanded:
                    continue

                collider_column = colliders_expanded_box.box().column()
                draw_spring_bone1_collider_layout(armature, collider_column, collider)
                remove_collider_op = layout_operator(
                    collider_column,
                    ops.VRM_OT_remove_spring_bone1_collider,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_collider_op.armature_name = armature.name
                remove_collider_op.collider_index = collider_index

        add_collider_op = layout_operator(
            colliders_box,
            ops.VRM_OT_add_spring_bone1_collider,
            icon="ADD",
        )
        add_collider_op.armature_name = armature.name

    collider_groups_box = layout.box()
    collider_groups_row = collider_groups_box.row()
    collider_groups_row.alignment = "LEFT"
    collider_groups_row.prop(
        spring_bone,
        "show_expanded_collider_groups",
        icon="TRIA_DOWN" if spring_bone.show_expanded_collider_groups else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone.show_expanded_collider_groups:
        if spring_bone.collider_groups:
            collider_groups_expanded_box = collider_groups_box.box().column()
            for collider_group_index, collider_group in enumerate(
                spring_bone.collider_groups
            ):
                collider_group_row = collider_groups_expanded_box.row()
                collider_group_row.alignment = "LEFT"
                collider_group_row.prop(
                    collider_group,
                    "show_expanded",
                    icon="TRIA_DOWN" if collider_group.show_expanded else "TRIA_RIGHT",
                    emboss=False,
                    text=collider_group.vrm_name,
                    translate=False,
                )

                if not collider_group.show_expanded:
                    continue

                collider_group_column = collider_groups_expanded_box.box().column()
                collider_group_column.prop(
                    collider_group,
                    "vrm_name",
                )

                collider_group_colliders_box = collider_group_column.box()
                if collider_group.colliders:
                    collider_group_colliders_row = collider_group_colliders_box.split(
                        factor=0.8
                    )
                    collider_group_colliders_names_column = (
                        collider_group_colliders_row.column()
                    )
                    for collider in collider_group.colliders:
                        collider_group_colliders_names_column.prop_search(
                            collider,
                            "collider_name",
                            spring_bone,
                            "colliders",
                            text="",
                            translate=False,
                        )
                    collider_group_colliders_buttons_column = (
                        collider_group_colliders_row.column()
                    )
                    for (
                        collider_index,
                        _,
                    ) in enumerate(collider_group.colliders):
                        remove_collider_group_collider_op = layout_operator(
                            collider_group_colliders_buttons_column,
                            ops.VRM_OT_remove_spring_bone1_collider_group_collider,
                            icon="REMOVE",
                            text="",
                            translate=False,
                        )
                        remove_collider_group_collider_op.armature_name = armature.name
                        remove_collider_group_collider_op.collider_group_index = (
                            collider_group_index
                        )
                        remove_collider_group_collider_op.collider_index = (
                            collider_index
                        )

                add_collider_group_collider_op = layout_operator(
                    collider_group_colliders_box,
                    ops.VRM_OT_add_spring_bone1_collider_group_collider,
                    icon="ADD",
                )
                add_collider_group_collider_op.armature_name = armature.name
                add_collider_group_collider_op.collider_group_index = (
                    collider_group_index
                )

                remove_collider_group_op = layout_operator(
                    collider_group_column,
                    ops.VRM_OT_remove_spring_bone1_collider_group,
                    icon="REMOVE",
                )
                remove_collider_group_op.armature_name = armature.name
                remove_collider_group_op.collider_group_index = collider_group_index

        add_collider_group_op = layout_operator(
            collider_groups_box,
            ops.VRM_OT_add_spring_bone1_collider_group,
            icon="ADD",
        )
        add_collider_group_op.armature_name = armature.name

    springs_box = layout.box()
    springs_row = springs_box.row()
    springs_row.alignment = "LEFT"
    springs_row.prop(
        spring_bone,
        "show_expanded_springs",
        icon="TRIA_DOWN" if spring_bone.show_expanded_springs else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone.show_expanded_springs:
        if spring_bone.springs:
            springs_expanded_box = springs_box.box().column()
            for spring_index, spring in enumerate(spring_bone.springs):
                spring_row = springs_expanded_box.row()
                spring_row.alignment = "LEFT"
                spring_row.prop(
                    spring,
                    "show_expanded",
                    icon="TRIA_DOWN" if spring.show_expanded else "TRIA_RIGHT",
                    emboss=False,
                    text=spring.vrm_name,
                    translate=False,
                )
                if not spring.show_expanded:
                    continue

                spring_column = springs_expanded_box.box().column()
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

                spring_joints_box = spring_column.box().column()
                if spring.joints:
                    for joint_index, joint in enumerate(spring.joints):
                        spring_joints_row = spring_joints_box.row()
                        spring_joints_row.alignment = "LEFT"
                        spring_joints_row.prop(
                            joint,
                            "show_expanded",
                            icon="TRIA_DOWN" if joint.show_expanded else "TRIA_RIGHT",
                            emboss=False,
                            text=joint.node.bone_name
                            if joint.node.bone_name
                            else "(EMPTY)",
                            translate=False,
                        )
                        if not joint.show_expanded:
                            continue

                        box = spring_joints_box.box().column()
                        box.prop_search(joint.node, "bone_name", armature_data, "bones")
                        box.prop(joint, "stiffness", slider=True)
                        box.prop(joint, "gravity_power", slider=True)
                        box.prop(joint, "gravity_dir")
                        box.prop(joint, "drag_force", slider=True)
                        box.prop(joint, "hit_radius", slider=True)

                        box.separator(factor=0.5)

                        remove_spring_joint_op = layout_operator(
                            box,
                            ops.VRM_OT_remove_spring_bone1_spring_joint,
                            icon="REMOVE",
                        )
                        remove_spring_joint_op.armature_name = armature.name
                        remove_spring_joint_op.spring_index = spring_index
                        remove_spring_joint_op.joint_index = joint_index

                add_spring_joint_op = layout_operator(
                    spring_joints_box,
                    ops.VRM_OT_add_spring_bone1_spring_joint,
                    icon="ADD",
                )
                add_spring_joint_op.armature_name = armature.name
                add_spring_joint_op.spring_index = spring_index
                add_spring_joint_op.guess_properties = True

                spring_collider_groups_box = spring_column.box()
                if spring.collider_groups:
                    spring_collider_groups_row = spring_collider_groups_box.split(
                        factor=0.8
                    )
                    spring_collider_groups_names_column = (
                        spring_collider_groups_row.column()
                    )
                    for collider_group in spring.collider_groups:
                        spring_collider_groups_names_column.prop_search(
                            collider_group,
                            "collider_group_name",
                            spring_bone,
                            "collider_groups",
                            text="",
                            translate=False,
                        )
                    spring_collider_groups_buttons_column = (
                        spring_collider_groups_row.column()
                    )
                    for (
                        collider_group_index,
                        _,
                    ) in enumerate(spring.collider_groups):
                        remove_spring_collider_group_op = layout_operator(
                            spring_collider_groups_buttons_column,
                            ops.VRM_OT_remove_spring_bone1_spring_collider_group,
                            icon="REMOVE",
                            text="",
                            translate=False,
                        )
                        remove_spring_collider_group_op.armature_name = armature.name
                        remove_spring_collider_group_op.spring_index = spring_index
                        remove_spring_collider_group_op.collider_group_index = (
                            collider_group_index
                        )

                add_spring_collider_group_op = layout_operator(
                    spring_collider_groups_box,
                    ops.VRM_OT_add_spring_bone1_spring_collider_group,
                    icon="ADD",
                )
                add_spring_collider_group_op.armature_name = armature.name
                add_spring_collider_group_op.spring_index = spring_index

                remove_spring_op = layout_operator(
                    spring_column,
                    ops.VRM_OT_remove_spring_bone1_spring,
                    icon="REMOVE",
                )
                remove_spring_op.armature_name = armature.name
                remove_spring_op.spring_index = spring_index

        add_spring_op = layout_operator(
            springs_box,
            ops.VRM_OT_add_spring_bone1_spring,
            icon="ADD",
        )
        add_spring_op.armature_name = armature.name


class VRM_PT_spring_bone1_armature_object_property(bpy.types.Panel):
    bl_idname = "VRM_PT_vrm1_spring_bone_armature_object_property"
    bl_label = "Spring Bone"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        draw_spring_bone1_spring_bone_layout(
            active_object,
            self.layout,
            armature_data.vrm_addon_extension.spring_bone1,
        )


class VRM_PT_spring_bone1_ui(bpy.types.Panel):
    bl_idname = "VRM_PT_vrm1_spring_bone_ui"
    bl_label = "Spring Bone"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        draw_spring_bone1_spring_bone_layout(
            armature,
            self.layout,
            armature_data.vrm_addon_extension.spring_bone1,
        )


class VRM_PT_spring_bone1_collider_property(bpy.types.Panel):
    bl_idname = "VRM_PT_spring_bone1_collider_property"
    bl_label = "VRM Spring Bone Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def active_armature_and_collider(
        cls, context: bpy.types.Context
    ) -> Optional[tuple[bpy.types.Object, SpringBone1ColliderPropertyGroup]]:
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
        for obj in bpy.data.objects:
            if obj.type != "ARMATURE":
                continue
            armature_data = obj.data
            if not isinstance(armature_data, bpy.types.Armature):
                continue
            for collider in armature_data.vrm_addon_extension.spring_bone1.colliders:
                if collider.bpy_object == collider_object:
                    return (obj, collider)
        return None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return cls.active_armature_and_collider(context) is not None

    def draw(self, context: bpy.types.Context) -> None:
        armature_and_collider = self.active_armature_and_collider(context)
        if armature_and_collider is None:
            return
        armature, collider = armature_and_collider
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        if armature_data.vrm_addon_extension.is_vrm1():
            draw_spring_bone1_collider_layout(armature, self.layout.column(), collider)
            return

        self.layout.label(text="This is a VRM 1.0 Spring Bone Collider", icon="INFO")
