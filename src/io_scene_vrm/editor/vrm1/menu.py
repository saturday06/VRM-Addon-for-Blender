# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Context, Menu, Object, UILayout

from ...common.logger import get_logger
from ..ops import layout_operator
from .ops import (
    VRM_OT_assign_vrm1_expressions_automatically,
    VRM_OT_assign_vrm1_expressions_from_arkit,
    VRM_OT_assign_vrm1_expressions_from_mmd,
    VRM_OT_assign_vrm1_expressions_from_ready_player_me,
    VRM_OT_assign_vrm1_expressions_from_vrchat,
    VRM_OT_restore_vrm1_expression_morph_target_bind_object,
)

logger = get_logger(__name__)


class VRM_MT_vrm1_expression(Menu):
    bl_label = "Expression Menu"
    bl_idname = "VRM_MT_vrm1_expression"

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

        restore_vrm1_expression_morph_target_bind_object_op = layout_operator(
            layout, VRM_OT_restore_vrm1_expression_morph_target_bind_object
        )
        restore_vrm1_expression_morph_target_bind_object_op.armature_object_name = (
            armature.name
        )

        auto_detection_op = layout_operator(
            layout, VRM_OT_assign_vrm1_expressions_automatically
        )
        auto_detection_op.armature_object_name = armature.name

        vrchat_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_expressions_from_vrchat
        )
        vrchat_expressions_op.armature_object_name = armature.name

        mmd_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_expressions_from_mmd
        )
        mmd_expressions_op.armature_object_name = armature.name

        ready_player_me_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_expressions_from_ready_player_me
        )
        ready_player_me_expressions_op.armature_object_name = armature.name

        arkit_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_expressions_from_arkit
        )
        arkit_expressions_op.armature_object_name = armature.name
