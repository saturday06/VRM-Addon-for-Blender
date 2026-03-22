# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Armature, Context, Menu, Object, UILayout

from ...common.logger import get_logger
from ..extension_accessor import get_armature_extension
from ..ops import layout_operator
from .ops import (
    VRM_OT_assign_vrm0_secondary_animation_group_collider_group,
    VRM_OT_restore_vrm0_blend_shape_group_bind_object,
    VRM_OT_unassign_vrm0_secondary_animation_group_collider_group,
)
from .property_group import (
    Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
)

logger = get_logger(__name__)


class VRM_MT_vrm0_blend_shape_master(Menu):
    bl_label = "Blend Shape Proxy Menu"
    bl_idname = "VRM_MT_vrm0_blend_shape_master"

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

        op = layout_operator(layout, VRM_OT_restore_vrm0_blend_shape_group_bind_object)
        op.armature_object_name = armature.name


class VRM_MT_vrm0_secondary_animation_group_collider_group(Menu):
    bl_label = "Collider Group Assignment Menu"
    bl_idname = "VRM_MT_vrm0_secondary_animation_group_collider_group"

    CONTEXT_POINTER_BONE_GROUP: Final = bl_idname + "_bone_group"
    CONTEXT_POINTER_COLLIDER_GROUP_REFERENCE: Final = (
        bl_idname + "_collider_group_reference"
    )

    @classmethod
    def draw_input_layout(
        cls,
        layout: UILayout,
        bone_group: Vrm0SecondaryAnimationGroupPropertyGroup,
        collider_group_reference: (
            Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup
        ),
        *,
        icon: str = "PIVOT_INDIVIDUAL",
    ) -> UILayout:
        row = layout.row(align=True)
        row.context_pointer_set(
            cls.CONTEXT_POINTER_BONE_GROUP,
            bone_group,
        )
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

        bone_group = getattr(context, self.CONTEXT_POINTER_BONE_GROUP, None)
        if not isinstance(
            bone_group,
            Vrm0SecondaryAnimationGroupPropertyGroup,
        ):
            return

        collider_group_reference = getattr(
            context, self.CONTEXT_POINTER_COLLIDER_GROUP_REFERENCE, None
        )
        if not isinstance(
            collider_group_reference,
            Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup,
        ):
            return

        armature_data = collider_group_reference.id_data
        if not isinstance(armature_data, Armature):
            return

        if bone_group.id_data != armature_data:
            return

        assigned_uuids: set[str] = {
            collider_group_reference.collider_group_uuid
            for collider_group_reference in bone_group.collider_groups
            if collider_group_reference.collider_group_uuid
        }

        vrm0 = get_armature_extension(armature_data).vrm0
        secondary_animation = vrm0.secondary_animation
        collider_group_reference_path = collider_group_reference.path_from_id()

        if collider_group_reference.collider_group_uuid:
            unassign_op = layout_operator(
                layout,
                VRM_OT_unassign_vrm0_secondary_animation_group_collider_group,
                text="<Unassign>",
                translate=True,
                icon="REMOVE",
            )
            unassign_op.armature_data_name = armature_data.name
            unassign_op.collider_group_reference_path = collider_group_reference_path

        for collider_group in secondary_animation.collider_groups:
            if not collider_group.uuid:
                continue
            if collider_group.uuid in assigned_uuids:
                continue

            assign_op = layout_operator(
                layout,
                VRM_OT_assign_vrm0_secondary_animation_group_collider_group,
                text=collider_group.display_name,
                translate=False,
                icon="PIVOT_INDIVIDUAL",
            )
            assign_op.armature_data_name = armature_data.name
            assign_op.collider_group_reference_path = collider_group_reference_path
            assign_op.collider_group_uuid = collider_group.uuid
