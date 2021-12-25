import bpy
from bpy.app.translations import pgettext

from ..common.preferences import get_preferences
from . import (
    detail_mesh_maker,
    glsl_drawer,
    make_armature,
    mesh_from_bone_envelopes,
    operator,
    search,
    validation,
)
from .extension import VrmAddonArmatureExtensionPropertyGroup
from .glsl_drawer import GlslDrawObj


class VRM_PT_vrm_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm_armature_object_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
            and isinstance(
                context.active_object.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        )

    def draw(self, _context: bpy.types.Context) -> None:
        pass


def add_armature(
    add_armature_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:
    add_armature_op.layout.operator(
        make_armature.ICYP_OT_make_armature.bl_idname,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    )


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


class VRM_PT_current_selected_armature(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
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


class VRM_PT_controller(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "Operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="OBJECT_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        mode = context.mode
        layout = self.layout
        object_type = active_object.type if active_object else None
        preferences = get_preferences(context)

        # region draw_main
        layout.operator(
            make_armature.ICYP_OT_make_armature.bl_idname,
            text=pgettext("Create VRM model"),
            icon="OUTLINER_OB_ARMATURE",
        )
        vrm_validator_prop = layout.operator(
            validation.WM_OT_vrm_validator.bl_idname,
            text=pgettext("Validate VRM model"),
            icon="VIEWZOOM",
        )
        vrm_validator_prop.show_successful_message = True
        if preferences:
            layout.prop(preferences, "export_invisibles")
            layout.prop(preferences, "export_only_selections")

        if mode == "OBJECT":
            if GlslDrawObj.draw_objs:
                layout.operator(
                    glsl_drawer.ICYP_OT_remove_draw_model.bl_idname,
                    icon="SHADING_RENDERED",
                    depress=True,
                )
            else:
                if [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
                    layout.operator(
                        glsl_drawer.ICYP_OT_draw_model.bl_idname,
                        icon="SHADING_RENDERED",
                        depress=False,
                    )
                else:
                    layout.label(text="Preview MToon")
                    layout.box().label(
                        icon="INFO",
                        text=pgettext("A light is required"),
                    )
            if object_type == "MESH":
                layout.operator(
                    operator.VRM_OT_vroid2vrc_lipsync_from_json_recipe.bl_idname,
                    icon="EXPERIMENTAL",
                )
        if mode == "EDIT_MESH":
            layout.operator(bpy.ops.mesh.symmetry_snap.idname_py(), icon="MOD_MIRROR")
        # endregion draw_main
