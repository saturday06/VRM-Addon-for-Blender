# SPDX-License-Identifier: MIT OR GPL-3.0-or-later


from typing import ClassVar

from bpy.types import Armature, Context, Panel

from .. import search
from ..extension import get_armature_extension
from ..khr_xmp_json_ld.panel import draw_khr_xmp_json_ld_packet_layout
from ..panel import VRM_PT_vrm_armature_object_property


class VRM_PT_khr_character_armature_object_property(Panel):
    bl_idname = "VRM_PT_khr_character_armature_object_property"
    bl_label = "XMP Linked Data"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options: ClassVar = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.active_object_is_khr_character_armature(context)

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object or active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_khr_xmp_json_ld_packet_layout(
            context,
            active_object,
            self.layout,
            ext.khr_character.khr_xmp_json_ld_packet,
        )


class VRM_PT_khr_character_ui(Panel):
    bl_idname = "VRM_PT_khr_character_ui"
    bl_label = "XMP Linked Data"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: ClassVar = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.active_object_is_khr_character_armature(context)

    def draw(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object or active_object.type != "ARMATURE":
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        draw_khr_xmp_json_ld_packet_layout(
            context,
            active_object,
            self.layout,
            ext.khr_character.khr_xmp_json_ld_packet,
        )
