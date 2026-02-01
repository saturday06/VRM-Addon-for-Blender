# SPDX-License-Identifier: MIT OR GPL-3.0-or-later


from typing import ClassVar

from bpy.types import Armature, Context, Object, Panel, UILayout

from .. import search
from ..extension import get_armature_extension
from ..panel import VRM_PT_vrm_armature_object_property
from .property_group import KhrCharacterPropertyGroup


def draw_khr_character_layout(
    _context: Context,
    _armature: Object,
    layout: UILayout,
    _khr_character: KhrCharacterPropertyGroup,
) -> None:
    box = layout.box()
    box.label(text="KHR Character Properties", icon="OUTLINER_OB_ARMATURE")


class VRM_PT_khr_character_armature_object_property(Panel):
    bl_idname = "VRM_PT_khr_character_armature_object_property"
    bl_label = "KHR Character"
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
        draw_khr_character_layout(
            context, active_object, self.layout, ext.khr_character
        )


class VRM_PT_khr_character_ui(Panel):
    bl_idname = "VRM_PT_khr_character_ui"
    bl_label = "KHR Character"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KHR Character / VRM"
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
        draw_khr_character_layout(
            context, active_object, self.layout, ext.khr_character
        )
