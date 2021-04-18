import bpy

from .. import lang, vrm_types
from ..preferences import get_preferences
from . import (
    detail_mesh_maker,
    glsl_drawer,
    make_armature,
    mesh_from_bone_envelopes,
    validation,
    vrm_helper,
)
from .glsl_drawer import GlslDrawObj


def add_armature(
    add_armature_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    add_armature_op.layout.operator(
        make_armature.ICYP_OT_MAKE_ARMATURE.bl_idname,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    )


def make_mesh(make_mesh_op: bpy.types.Operator, context: bpy.types.Context) -> None:
    make_mesh_op.layout.separator()
    make_mesh_op.layout.operator(
        mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES.bl_idname,
        text="Mesh from selected armature",
        icon="PLUGIN",
    )
    make_mesh_op.layout.operator(
        detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER.bl_idname,
        text="(WIP)Face mesh from selected armature and bound mesh",
        icon="PLUGIN",
    )


class VRM_IMPORTER_PT_controller(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "VRM Helper"
    # どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.active_object)

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        mode = context.mode
        layout = self.layout
        object_type = active_object.type
        data = active_object.data

        # region helper
        def armature_ui() -> None:
            layout.separator()
            armature_box = layout.row(align=False).box()
            armature_box.label(text="Armature Help")
            armature_box.operator(vrm_helper.Add_VRM_extensions_to_armature.bl_idname)
            layout.separator()

            requires_box = armature_box.box()
            requires_box.label(text="VRM Required Bones", icon="ARMATURE_DATA")
            for req in vrm_types.HumanBones.center_req[::-1]:
                icon = "USER"
                if req in data:
                    requires_box.prop_search(
                        data, f'["{req}"]', data, "bones", text=req, icon=icon
                    )
                else:
                    requires_box.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                        icon="ADD",
                    )
            row = requires_box.row()
            column = row.column()
            for req in vrm_types.HumanBones.right_arm_req:
                icon = "VIEW_PAN"
                if req in data:
                    column.prop_search(
                        data, f'["{req}"]', data, "bones", text=req, icon=icon
                    )
                else:
                    column.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                        icon="ADD",
                    )
            column = row.column()
            for req in vrm_types.HumanBones.left_arm_req:
                icon = "VIEW_PAN"
                if req in data:
                    column.prop_search(
                        data, f'["{req}"]', data, "bones", text=req, icon=icon
                    )
                else:
                    column.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                        icon="ADD",
                    )
            row = requires_box.row()
            column = row.column()
            for req in vrm_types.HumanBones.right_leg_req:
                icon = "HANDLE_AUTO"
                if req in data:
                    column.prop_search(
                        data, f'["{req}"]', data, "bones", text=req, icon=icon
                    )
                else:
                    column.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                        icon="ADD",
                    )
            column = row.column()
            for req in vrm_types.HumanBones.left_leg_req:
                icon = "HANDLE_AUTO"
                if req in data:
                    column.prop_search(
                        data, f'["{req}"]', data, "bones", text=req, icon=icon
                    )
                else:
                    column.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                        icon="ADD",
                    )
            defines_box = armature_box.box()
            defines_box.label(text="VRM Optional Bones", icon="BONE_DATA")
            row = defines_box.row()
            for defs in ["rightEye"]:
                icon = "HIDE_OFF"
                if defs in data:
                    row.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    row.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            for defs in ["leftEye"]:
                icon = "HIDE_OFF"
                if defs in data:
                    row.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    row.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            for defs in vrm_types.HumanBones.center_def[::-1]:
                icon = "USER"
                if defs in data:
                    defines_box.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            defines_box.separator()
            for defs in vrm_types.HumanBones.right_arm_def:
                icon = "VIEW_PAN"
                if defs in data:
                    defines_box.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            for defs in vrm_types.HumanBones.right_leg_def:
                icon = "HANDLE_AUTO"
                if defs in data:
                    defines_box.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            defines_box.separator()
            for defs in vrm_types.HumanBones.left_arm_def:
                icon = "VIEW_PAN"
                if defs in data:
                    defines_box.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            for defs in vrm_types.HumanBones.left_leg_def:
                icon = "HANDLE_AUTO"
                if defs in data:
                    defines_box.prop_search(
                        data, f'["{defs}"]', data, "bones", text=defs, icon=icon
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                        icon="ADD",
                    )
            armature_box.label(icon="EXPERIMENTAL", text="EXPERIMENTAL!!!")
            armature_box.operator(vrm_helper.Bones_rename.bl_idname)

        # endregion helper

        # region draw_main
        if mode == "OBJECT":
            object_mode_box = layout.box()
            preferences = get_preferences(context)
            if preferences:
                object_mode_box.prop(
                    preferences,
                    "export_invisibles",
                    text=lang.support("Export invisible objects", "非表示オブジェクトを含める"),
                )
                object_mode_box.prop(
                    preferences,
                    "export_only_selections",
                    text=lang.support("Export only selections", "選択されたオブジェクトのみ"),
                )
            vrm_validator_prop = object_mode_box.operator(
                validation.WM_OT_vrmValidator.bl_idname,
                text=lang.support("Validate VRM model", "VRMモデルのチェック"),
            )
            vrm_validator_prop.show_successful_message = True
            # vrm_validator_prop.errors = []  # これはできない
            object_mode_box.label(text="MToon preview")
            if [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
                object_mode_box.operator(glsl_drawer.ICYP_OT_Draw_Model.bl_idname)
            else:
                object_mode_box.box().label(
                    icon="INFO",
                    text=lang.support("A light is required", "ライトが必要です"),
                )
            if GlslDrawObj.draw_objs:
                object_mode_box.operator(
                    glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname
                )
            if object_type == "ARMATURE":
                armature_ui()
            if object_type == "MESH":
                layout.label(icon="EXPERIMENTAL", text="EXPERIMENTAL!!!")
                layout.operator(vrm_helper.Vroid2VRC_lipsync_from_json_recipe.bl_idname)
        if mode == "EDIT_MESH":
            layout.operator(bpy.ops.mesh.symmetry_snap.idname_py())

        if mode == "POSE" and object_type == "ARMATURE":
            armature_ui()
        # endregion draw_main
