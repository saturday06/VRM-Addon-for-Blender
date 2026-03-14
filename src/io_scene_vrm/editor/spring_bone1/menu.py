# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Callable
from typing import Final

from bpy.types import Context, Menu, Object, UILayout

from ..ops import layout_operator
from .ops import VRM_OT_assign_spring_bone1_from_vrm0


class VRM_MT_vrm1_spring_bone(Menu):
    bl_label = "Spring Bone Menu"
    bl_idname = "VRM_MT_vrm1_spring_bone"

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

        assign_op = layout_operator(layout, VRM_OT_assign_spring_bone1_from_vrm0)
        assign_op.armature_object_name = armature.name
