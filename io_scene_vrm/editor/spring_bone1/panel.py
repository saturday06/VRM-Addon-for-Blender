import bpy

from .. import search
from ..extension import VrmAddonArmatureExtensionPropertyGroup
from ..migration import migrate
from ..panel import VRM_PT_vrm_armature_object_property
from . import operator as vrm1_operator
from .property_group import SpringBone1SpringBonePropertyGroup


def active_object_is_vrm1_armature(context: bpy.types.Context) -> bool:
    return bool(
        context
        and context.active_object
        and context.active_object.type == "ARMATURE"
        and hasattr(context.active_object.data, "vrm_addon_extension")
        and isinstance(
            context.active_object.data.vrm_addon_extension,
            VrmAddonArmatureExtensionPropertyGroup,
        )
        and context.active_object.data.vrm_addon_extension.is_vrm1()
    )


def draw_vrm1_spring_bone_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    spring_bone: SpringBone1SpringBonePropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

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
                collider_column.prop(
                    collider.bpy_object, "name", icon="MESH_UVSPHERE", text=""
                )
                collider_column.prop(collider.shape, "shape")
                collider_column.prop_search(
                    collider.node, "value", armature.data, "bones"
                )
                remove_collider_op = collider_column.operator(
                    vrm1_operator.VRM_OT_remove_spring_bone1_collider.bl_idname,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_collider_op.armature_data_name = armature.data.name
                remove_collider_op.collider_index = collider_index

        add_collider_op = colliders_box.operator(
            vrm1_operator.VRM_OT_add_spring_bone1_collider.bl_idname,
            icon="ADD",
        )
        add_collider_op.armature_data_name = armature.data.name

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
                        remove_collider_group_collider_op = collider_group_colliders_buttons_column.operator(
                            vrm1_operator.VRM_OT_remove_spring_bone1_collider_group_collider.bl_idname,
                            icon="REMOVE",
                            text="",
                            translate=False,
                        )
                        remove_collider_group_collider_op.armature_data_name = (
                            armature.data.name
                        )
                        remove_collider_group_collider_op.collider_group_index = (
                            collider_group_index
                        )
                        remove_collider_group_collider_op.collider_index = (
                            collider_index
                        )

                add_collider_group_collider_op = collider_group_colliders_box.operator(
                    vrm1_operator.VRM_OT_add_spring_bone1_collider_group_collider.bl_idname,
                    icon="ADD",
                )
                add_collider_group_collider_op.armature_data_name = armature.data.name
                add_collider_group_collider_op.collider_group_index = (
                    collider_group_index
                )

                remove_collider_group_op = collider_group_column.operator(
                    vrm1_operator.VRM_OT_remove_spring_bone1_collider_group.bl_idname,
                    icon="REMOVE",
                )
                remove_collider_group_op.armature_data_name = armature.data.name
                remove_collider_group_op.collider_group_index = collider_group_index

        add_collider_group_op = collider_groups_box.operator(
            vrm1_operator.VRM_OT_add_spring_bone1_collider_group.bl_idname,
            icon="ADD",
        )
        add_collider_group_op.armature_data_name = armature.data.name

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
                            text=joint.node.value if joint.node.value else "(EMPTY)",
                            translate=False,
                        )
                        if not joint.show_expanded:
                            continue
                        box = spring_joints_box.box().column()
                        box.prop_search(joint.node, "value", armature.data, "bones")
                        box.prop(joint, "hit_radius")
                        box.prop(joint, "stiffness")
                        box.prop(joint, "gravity_power")
                        box.prop(joint, "gravity_dir")
                        box.prop(joint, "drag_force")

                        remove_spring_joint_op = box.operator(
                            vrm1_operator.VRM_OT_remove_spring_bone1_spring_joint.bl_idname,
                            icon="REMOVE",
                        )
                        remove_spring_joint_op.armature_data_name = armature.data.name
                        remove_spring_joint_op.spring_index = spring_index
                        remove_spring_joint_op.joint_index = joint_index

                add_spring_joint_op = spring_joints_box.operator(
                    vrm1_operator.VRM_OT_add_spring_bone1_spring_joint.bl_idname,
                    icon="ADD",
                )
                add_spring_joint_op.armature_data_name = armature.data.name
                add_spring_joint_op.spring_index = spring_index

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
                        remove_spring_collider_group_op = spring_collider_groups_buttons_column.operator(
                            vrm1_operator.VRM_OT_remove_spring_bone1_spring_collider_group.bl_idname,
                            icon="REMOVE",
                            text="",
                            translate=False,
                        )
                        remove_spring_collider_group_op.armature_data_name = (
                            armature.data.name
                        )
                        remove_spring_collider_group_op.spring_index = spring_index
                        remove_spring_collider_group_op.collider_group_index = (
                            collider_group_index
                        )

                add_spring_collider_group_op = spring_collider_groups_box.operator(
                    vrm1_operator.VRM_OT_add_spring_bone1_spring_collider_group.bl_idname,
                    icon="ADD",
                )
                add_spring_collider_group_op.armature_data_name = armature.data.name
                add_spring_collider_group_op.spring_index = spring_index

                remove_spring_op = spring_column.operator(
                    vrm1_operator.VRM_OT_remove_spring_bone1_spring.bl_idname,
                    icon="REMOVE",
                )
                remove_spring_op.armature_data_name = armature.data.name
                remove_spring_op.spring_index = spring_index

        add_spring_op = springs_box.operator(
            vrm1_operator.VRM_OT_add_spring_bone1_spring.bl_idname,
            icon="ADD",
        )
        add_spring_op.armature_data_name = armature.data.name


class VRM_PT_spring_bone1_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_spring_bone_armature_object_property"
    bl_label = "Spring Bone"
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
        draw_vrm1_spring_bone_layout(
            context.active_object,
            self.layout,
            context.active_object.data.vrm_addon_extension.spring_bone1,
        )


class VRM_PT_spring_bone1_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_spring_bone_ui"
    bl_label = "Spring Bone"
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
        draw_vrm1_spring_bone_layout(
            armature,
            self.layout,
            armature.data.vrm_addon_extension.spring_bone1,
        )
