# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Armature, Context, Menu, Object, UILayout

from ..extension_accessor import get_armature_extension
from ..ops import layout_operator
from .ops import (
    VRM_OT_assign_spring_bone1_automatically,
    VRM_OT_assign_spring_bone1_collider_group_collider,
    VRM_OT_assign_spring_bone1_from_mmd,
    VRM_OT_assign_spring_bone1_from_vrm0,
    VRM_OT_assign_spring_bone1_spring_collider_group,
    VRM_OT_unassign_spring_bone1_collider_group_collider,
    VRM_OT_unassign_spring_bone1_spring_collider_group,
)
from .property_group import (
    SpringBone1ColliderGroupReferencePropertyGroup,
    SpringBone1ColliderReferencePropertyGroup,
)


class VRM_MT_spring_bone1_spring_bones(Menu):
    bl_label = "Spring Bone Menu"
    bl_idname = "VRM_MT_spring_bone1_spring_bones"

    CONTEXT_POINTER_ARMATURE: Final = bl_idname + "_armature"

    @classmethod
    def layout_context_pointer_set(cls, armature: Object) -> Callable[[UILayout], None]:
        return lambda layout: layout.context_pointer_set(
            cls.CONTEXT_POINTER_ARMATURE, armature
        )

    def draw(self, context: Context) -> None:
        layout = self.layout

        armature = getattr(context, self.CONTEXT_POINTER_ARMATURE, None)
        if not isinstance(armature, Object):
            return

        auto_detection_op = layout_operator(
            layout, VRM_OT_assign_spring_bone1_automatically
        )
        auto_detection_op.armature_object_name = armature.name

        assign_op = layout_operator(layout, VRM_OT_assign_spring_bone1_from_vrm0)
        assign_op.armature_object_name = armature.name

        assign_mmd_op = layout_operator(layout, VRM_OT_assign_spring_bone1_from_mmd)
        assign_mmd_op.armature_object_name = armature.name


class VRM_MT_spring_bone1_collider_group_collider(Menu):
    bl_label = "Collider Assignment Menu"
    bl_idname = "VRM_MT_spring_bone1_collider_group_collider"

    CONTEXT_POINTER_COLLIDER_REFERENCE: Final = bl_idname + "_collider_reference"

    @classmethod
    def draw_input_layout(
        cls,
        layout: UILayout,
        collider_reference: SpringBone1ColliderReferencePropertyGroup,
        *,
        icon: str = "SPHERE",
    ) -> UILayout:
        row = layout.row(align=True)
        row.context_pointer_set(
            cls.CONTEXT_POINTER_COLLIDER_REFERENCE,
            collider_reference,
        )
        row.menu(
            cls.bl_idname,
            text=collider_reference.collider_display_name or " ",
            icon=icon,
            translate=False,
        )
        return row

    def draw(self, context: Context) -> None:
        layout = self.layout

        collider_reference = getattr(
            context, self.CONTEXT_POINTER_COLLIDER_REFERENCE, None
        )
        if not isinstance(
            collider_reference, SpringBone1ColliderReferencePropertyGroup
        ):
            return

        armature_data = collider_reference.id_data
        if not isinstance(armature_data, Armature):
            return

        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        collider_reference_path = collider_reference.path_from_id()

        if collider_reference.collider_uuid:
            unassign_op = layout_operator(
                layout,
                VRM_OT_unassign_spring_bone1_collider_group_collider,
                text="<Unassign>",
                translate=True,
                icon="REMOVE",
            )
            unassign_op.armature_data_name = armature_data.name
            unassign_op.collider_reference_path = collider_reference_path

        for collider in spring_bone1.colliders:
            if not collider.uuid:
                continue
            if collider.uuid == collider_reference.collider_uuid:
                continue

            assign_op = layout_operator(
                layout,
                VRM_OT_assign_spring_bone1_collider_group_collider,
                text=collider.display_name,
                translate=False,
                icon="SPHERE",
            )
            assign_op.armature_data_name = armature_data.name
            assign_op.collider_reference_path = collider_reference_path
            assign_op.collider_uuid = collider.uuid


class VRM_MT_spring_bone1_spring_collider_group(Menu):
    bl_label = "Collider Group Assignment Menu"
    bl_idname = "VRM_MT_spring_bone1_spring_collider_group"

    CONTEXT_POINTER_COLLIDER_GROUP_REFERENCE: Final = (
        bl_idname + "_collider_group_reference"
    )

    @classmethod
    def draw_input_layout(
        cls,
        layout: UILayout,
        collider_group_reference: SpringBone1ColliderGroupReferencePropertyGroup,
        *,
        icon: str = "PIVOT_INDIVIDUAL",
    ) -> UILayout:
        row = layout.row(align=True)
        row.context_pointer_set(
            cls.CONTEXT_POINTER_COLLIDER_GROUP_REFERENCE,
            collider_group_reference,
        )
        row.menu(
            cls.bl_idname,
            text=collider_group_reference.collider_group_display_name or " ",
            icon=icon,
            translate=False,
        )
        return row

    def draw(self, context: Context) -> None:
        layout = self.layout

        collider_group_reference = getattr(
            context, self.CONTEXT_POINTER_COLLIDER_GROUP_REFERENCE, None
        )
        if not isinstance(
            collider_group_reference,
            SpringBone1ColliderGroupReferencePropertyGroup,
        ):
            return

        armature_data = collider_group_reference.id_data
        if not isinstance(armature_data, Armature):
            return

        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        collider_group_reference_path = collider_group_reference.path_from_id()

        if collider_group_reference.collider_group_uuid:
            unassign_op = layout_operator(
                layout,
                VRM_OT_unassign_spring_bone1_spring_collider_group,
                text="<Unassign>",
                translate=True,
                icon="REMOVE",
            )
            unassign_op.armature_data_name = armature_data.name
            unassign_op.collider_group_reference_path = collider_group_reference_path

        for index, collider_group in enumerate(spring_bone1.collider_groups):
            if not collider_group.uuid:
                continue
            if collider_group.uuid == collider_group_reference.collider_group_uuid:
                continue

            assign_op = layout_operator(
                layout,
                VRM_OT_assign_spring_bone1_spring_collider_group,
                text=f"{index + 1}: " + collider_group.vrm_name,
                translate=False,
                icon="PIVOT_INDIVIDUAL",
            )
            assign_op.armature_data_name = armature_data.name
            assign_op.collider_group_reference_path = collider_group_reference_path
            assign_op.collider_group_uuid = collider_group.uuid
