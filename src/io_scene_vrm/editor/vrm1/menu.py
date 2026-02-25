# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Context, Menu, Object, UILayout

from ...common.logger import get_logger
from ..ops import layout_operator
from .ops import (
    VRM_OT_add_vrm1_arkit_custom_expressions,
    VRM_OT_assign_vrm1_expressions_automatically,
    VRM_OT_assign_vrm1_mmd_expressions,
    VRM_OT_assign_vrm1_ready_player_me_expressions,
    VRM_OT_assign_vrm1_vrchat_expressions,
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

        add_vrchat_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_vrchat_expressions
        )
        add_vrchat_expressions_op.armature_object_name = armature.name

        add_mmd_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_mmd_expressions
        )
        add_mmd_expressions_op.armature_object_name = armature.name

        add_ready_player_me_expressions_op = layout_operator(
            layout, VRM_OT_assign_vrm1_ready_player_me_expressions
        )
        add_ready_player_me_expressions_op.armature_object_name = armature.name

        add_arkit_expressions_op = layout_operator(
            layout, VRM_OT_add_vrm1_arkit_custom_expressions
        )
        add_arkit_expressions_op.armature_object_name = armature.name
