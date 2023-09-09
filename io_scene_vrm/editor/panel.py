import bpy
from bpy.app.translations import pgettext

from ..common import version
from ..common.preferences import get_preferences
from . import (
    detail_mesh_maker,
    make_armature,
    mesh_from_bone_envelopes,
    search,
    validation,
)
from .ops import layout_operator


class VRM_PT_vrm_armature_object_property(bpy.types.Panel):
    bl_idname = "VRM_PT_vrm_armature_object_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_object = context.active_object
        if not active_object:
            return False
        armature_data = active_object.data
        return isinstance(armature_data, bpy.types.Armature)

    def draw(self, _context: bpy.types.Context) -> None:
        warning_message = version.panel_warning_message()
        if not warning_message:
            return

        box = self.layout.box()
        warning_column = box.column()
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )


def add_armature(
    add_armature_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:
    layout_operator(
        add_armature_op.layout,
        make_armature.ICYP_OT_make_armature,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    ).skip_heavy_armature_setup = True


def make_mesh(make_mesh_op: bpy.types.Operator, _context: bpy.types.Context) -> None:
    make_mesh_op.layout.separator()
    make_mesh_op.layout.operator(
        mesh_from_bone_envelopes.ICYP_OT_make_mesh_from_bone_envelopes.bl_idname,
        text="Mesh from selected armature",
        icon="PLUGIN",
    )
    make_mesh_op.layout.operator(
        detail_mesh_maker.ICYP_OT_detail_mesh_maker.bl_idname,
        text="(WIP)Face mesh from selected armature and bound mesh",
        icon="PLUGIN",
    )


class VRM_PT_current_selected_armature(bpy.types.Panel):
    bl_idname = "VRM_PT_current_selected_armature"
    bl_label = "Current selected armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.multiple_armatures_exist(context)

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        layout = self.layout
        layout.label(text=armature.name, icon="ARMATURE_DATA", translate=False)


class VRM_PT_controller(bpy.types.Panel):
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "Operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="TOOL_SETTINGS")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        preferences = get_preferences(context)

        # draw_main
        layout_operator(
            layout,
            make_armature.ICYP_OT_make_armature,
            text=pgettext("Create VRM Model"),
            icon="OUTLINER_OB_ARMATURE",
        ).skip_heavy_armature_setup = True
        vrm_validator_op = layout_operator(
            layout,
            validation.WM_OT_vrm_validator,
            text=pgettext("Validate VRM Model"),
            icon="VIEWZOOM",
        )
        vrm_validator_op.show_successful_message = True
        layout.prop(preferences, "export_invisibles")
        layout.prop(preferences, "export_only_selections")

        armature = search.current_armature(context)
        if armature:
            vrm_validator_op.armature_object_name = armature.name
            armature_data = armature.data
            if isinstance(armature_data, bpy.types.Armature):
                layout.prop(
                    armature_data.vrm_addon_extension,
                    "spec_version",
                    text="",
                    translate=False,
                )


class VRM_PT_controller_unsupported_blender_version_warning(bpy.types.Panel):
    bl_idname = "VRM_PT_controller_unsupported_blender_version_warning"
    bl_label = "Unsupported Blender Version Warning"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return bool(version.panel_warning_message())

    def draw(self, _context: bpy.types.Context) -> None:
        warning_message = version.panel_warning_message()
        if warning_message is None:
            return
        box = self.layout.box()
        warning_column = box.column()
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )
