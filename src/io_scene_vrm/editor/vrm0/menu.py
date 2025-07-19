# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, Menu

from ...common.logger import get_logger
from ..ops import layout_operator
from ..search import current_armature
from .ops import VRM_OT_restore_vrm0_blend_shape_group_bind_object

logger = get_logger(__name__)


class VRM_MT_vrm0_blend_shape_master(Menu):
    bl_label = "Blend Shape Proxy Menu"
    bl_idname = "VRM_MT_vrm0_blend_shape_master"

    def draw(self, context: Context) -> None:
        layout = self.layout

        armature = current_armature(context)
        if not armature:
            return

        op = layout_operator(layout, VRM_OT_restore_vrm0_blend_shape_group_bind_object)
        op.armature_object_name = armature.name
