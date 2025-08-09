# SPDX-License-Identifier: MIT OR GPL-3.0-or-later


from collections.abc import Set as AbstractSet

from bpy.types import Armature, Context, Panel

from ..extension import get_armature_extension
from ..khr_xmp_json_ld.panel import draw_khr_xmp_json_ld_khr_avatar_packet_layout
from ..panel import VRM_PT_vrm_armature_object_property
from ..search import active_object_is_khr_avatar_armature


class VRM_PT_vrm0_humanoid_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm0_humanoid_armature_object_property"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return active_object_is_khr_avatar_armature(context)

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        draw_khr_xmp_json_ld_khr_avatar_packet_layout(
            active_object,
            context,
            self.layout,
            get_armature_extension(armature_data).khr_avatar.khr_xmp_json_ld_packet,
        )
