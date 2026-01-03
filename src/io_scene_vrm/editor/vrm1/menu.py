# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Context, Menu, Object, UILayout

from ...common.logger import get_logger
from ..ops import layout_operator
from .ops import VRM_OT_restore_vrm1_expression_morph_target_bind_object

logger = get_logger(__name__)


class VRM_MT_vrm1_expression(Menu):
    bl_label = "Expression Menu"
    bl_idname = "VRM_MT_vrm1_expression"

    CONTEXT_POINTER_ARMATURE: Final = bl_idname + "_armature"

    @classmethod
    def setup_menu(cls, armature: Object) -> Callable[[UILayout], None]:
        return lambda layout: layout.context_pointer_set(
            cls.CONTEXT_POINTER_ARMATURE, armature
        )

    def draw(self, context: Context) -> None:
        layout = self.layout

        armature = getattr(context, self.CONTEXT_POINTER_ARMATURE, None)
        if not isinstance(armature, Object):
            return

        op = layout_operator(
            layout, VRM_OT_restore_vrm1_expression_morph_target_bind_object
        )
        op.armature_object_name = armature.name
