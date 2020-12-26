"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import os
import traceback
from typing import Set

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import vrm_types
from .importer import blend_model, vrm_load
from .misc import (
    detail_mesh_maker,
    glb_factory,
    glsl_drawer,
    make_armature,
    mesh_from_bone_envelopes,
    version,
    vrm_helper,
)

bl_info = {
    "name": "VRM_IMPORTER",
    "author": "saturday06, iCyP",
    # I'd like to use version.version(). But that is not allowed.
    "version": (0, 104, 0),
    "blender": (2, 82, 0),
    "location": "File->Import",
    "description": "VRM Importer",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export",
}

# Sanity check
if bl_info["version"] != version.version():
    raise Exception(f'Version mismatch: {bl_info["version"]} != {version.version()}')


class LicenseConfirmation(bpy.types.PropertyGroup):
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]


class ImportVRM(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    make_new_texture_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Make new texture folder (limit:10)"  # noqa: F722
    )
    is_put_spring_bone_info: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Put Collider Empty"  # noqa: F722
    )
    import_normal: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Normal"  # noqa: F722
    )
    remove_doubles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Remove doubles"  # noqa: F722
    )
    set_bone_roll: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Set bone roll"  # noqa: F722
    )
    use_simple_principled_material: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Use simple principled material"  # noqa: F722
    )
    use_in_blender: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="NOTHING TO DO in CURRENT use in blender"  # noqa: F722
    )

    def execute(self, context):
        license_error = None
        try:
            return create_blend_model(
                self,
                context,
                vrm_load.read_vrm(
                    self.filepath,
                    self.make_new_texture_folder,
                    self.use_simple_principled_material,
                    license_check=True,
                ),
            )
        except vrm_load.LicenseConfirmationRequired as e:
            license_error = e  # Prevent traceback dump on another exception

        print(license_error.description())

        execution_context = "INVOKE_DEFAULT"
        import_anyway = False
        if os.environ.get("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION") == "true":
            execution_context = "EXEC_DEFAULT"
            import_anyway = True

        return bpy.ops.wm.vrm_license_warning(
            execution_context,
            import_anyway=import_anyway,
            license_confirmations=license_error.license_confirmations(),
            filepath=self.filepath,
            make_new_texture_folder=self.make_new_texture_folder,
            is_put_spring_bone_info=self.is_put_spring_bone_info,
            import_normal=self.import_normal,
            remove_doubles=self.remove_doubles,
            set_bone_roll=self.set_bone_roll,
            use_simple_principled_material=self.use_simple_principled_material,
            use_in_blender=self.use_in_blender,
        )


def create_blend_model(addon, context, vrm_pydata: vrm_types.VrmPydata) -> Set[str]:
    has_ui_localization = bpy.app.version < (2, 83)
    ui_localization = False
    if has_ui_localization:
        ui_localization = bpy.context.preferences.view.use_international_fonts
    try:
        blend_model.BlendModel(
            context,
            vrm_pydata,
            addon.filepath,
            addon.is_put_spring_bone_info,
            addon.import_normal,
            addon.remove_doubles,
            addon.use_simple_principled_material,
            addon.set_bone_roll,
            addon.use_in_blender,
        )
    finally:
        if has_ui_localization and ui_localization:
            bpy.context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def menu_import(self, context):  # Same as test/io.py for now
    op = self.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")
    op.make_new_texture_folder = True
    op.is_put_spring_bone_info = True
    op.import_normal = True
    op.remove_doubles = False
    op.set_bone_roll = True


class ExportVRM(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    # vrm_version : bpy.props.EnumProperty(name="VRM version" ,items=(("0.0","0.0",""),("1.0","1.0","")))

    def execute(self, context):
        try:
            glb_obj = glb_factory.GlbObj()
        except glb_factory.GlbObj.ValidationError:
            return {"CANCELLED"}
        # vrm_bin =  glb_obj().convert_bpy2glb(self.vrm_version)
        vrm_bin = glb_obj.convert_bpy2glb("0.0")
        with open(self.filepath, "wb") as f:
            f.write(vrm_bin)
        return {"FINISHED"}


def menu_export(self, context):
    self.layout.operator(ExportVRM.bl_idname, text="VRM (.vrm)")


def add_armature(self, context):
    self.layout.operator(
        make_armature.ICYP_OT_MAKE_ARMATURE.bl_idname, text="VRM Humanoid"
    )


def make_mesh(self, context):
    self.layout.separator()
    self.layout.operator(
        mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES.bl_idname,
        text="Mesh from selected armature",
        icon="PLUGIN",
    )
    self.layout.operator(
        detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER.bl_idname,
        text="(WIP)Face mesh from selected armature and bound mesh",
        icon="PLUGIN",
    )


class VRM_IMPORTER_PT_controller(bpy.types.Panel):  # noqa: N801
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "VRM Helper"
    # どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM HELPER"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        # region helper
        def armature_ui():
            self.layout.separator()
            armature_box = self.layout.row(align=False).box()
            armature_box.label(text="Armature Help")
            armature_box.operator(vrm_helper.Add_VRM_extensions_to_armature.bl_idname)
            self.layout.separator()

            requires_box = armature_box.box()
            requires_row = requires_box.row()
            requires_row.label(text="VRM Required Bones")
            for req in vrm_types.HumanBones.requires:
                if req in context.active_object.data:
                    requires_box.prop_search(
                        context.active_object.data,
                        f'["{req}"]',
                        context.active_object.data,
                        "bones",
                        text=req,
                    )
                else:
                    requires_box.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                    )
            defines_box = armature_box.box()
            defines_box.label(text="VRM Optional Bones")
            for defs in vrm_types.HumanBones.defines:
                if defs in context.active_object.data:
                    defines_box.prop_search(
                        context.active_object.data,
                        f'["{defs}"]',
                        context.active_object.data,
                        "bones",
                        text=defs,
                    )
                else:
                    defines_box.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                    )

            armature_box.label(icon="ERROR", text="EXPERIMENTAL!!!")
            armature_box.operator(vrm_helper.Bones_rename.bl_idname)

        # endregion helper

        # region draw_main
        self.layout.label(text="If you select armature in object mode")
        self.layout.label(text="armature renamer is shown")
        self.layout.label(text="If you in MESH EDIT")
        self.layout.label(text="symmetry button is shown")
        self.layout.label(text="*Symmetry is in default blender function")
        if context.mode == "OBJECT" and context.active_object is not None:
            self.layout.operator(vrm_helper.VRM_VALIDATOR.bl_idname)
            mtoon_preview_box = self.layout.box()
            mtoon_preview_box.label(text="MToon preview")
            mtoon_preview_box.operator(glsl_drawer.ICYP_OT_Draw_Model.bl_idname)
            mtoon_preview_box.operator(glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname)
            if context.active_object.type == "ARMATURE":
                armature_ui()
            if context.active_object.type == "MESH":
                self.layout.label(icon="ERROR", text="EXPERIMENTAL!!!")
                self.layout.operator(
                    vrm_helper.Vroid2VRC_lipsync_from_json_recipe.bl_idname
                )

        if context.mode == "EDIT_MESH":
            self.layout.operator(bpy.ops.mesh.symmetry_snap.idname_py())

        if context.mode == "POSE" and context.active_object.type == "ARMATURE":
            armature_ui()
        # endregion draw_main


class WM_OT_licenseConfirmation(bpy.types.Operator):  # noqa: N801
    bl_label = "License confirmation"
    bl_idname = "wm.vrm_license_warning"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty()  # type: ignore[valid-type]

    license_confirmations: bpy.props.CollectionProperty(type=LicenseConfirmation)  # type: ignore[valid-type]
    import_anyway: bpy.props.BoolProperty()  # type: ignore[valid-type]

    make_new_texture_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]
    is_put_spring_bone_info: bpy.props.BoolProperty()  # type: ignore[valid-type]
    import_normal: bpy.props.BoolProperty()  # type: ignore[valid-type]
    remove_doubles: bpy.props.BoolProperty()  # type: ignore[valid-type]
    set_bone_roll: bpy.props.BoolProperty()  # type: ignore[valid-type]
    use_simple_principled_material: bpy.props.BoolProperty()  # type: ignore[valid-type]
    use_in_blender: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def execute(self, context):
        if not self.import_anyway:
            return {"CANCELLED"}
        return create_blend_model(
            self,
            context,
            vrm_load.read_vrm(
                self.filepath,
                self.make_new_texture_folder,
                self.use_simple_principled_material,
                license_check=False,
            ),
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.filepath)
        for license_confirmation in self.license_confirmations:
            for line in license_confirmation.message.split("\n"):
                layout.label(text=line)
            if license_confirmation.json_key:
                layout.label(
                    text=vrm_helper.lang_support(
                        "For more information please check following URL.",
                        "詳しくは下記のURLを確認してください。",
                    )
                )
                layout.prop(
                    license_confirmation,
                    "url",
                    text=license_confirmation.json_key,
                )
        layout.prop(
            self,
            "import_anyway",
            text=vrm_helper.lang_support("Import anyway", "インポートします"),
        )


@persistent
def add_shaders(self):
    filedir = os.path.join(
        os.path.dirname(__file__), "resources", "material_node_groups.blend"
    )
    with bpy.data.libraries.load(filedir, link=False) as (data_from, data_to):
        for nt in data_from.node_groups:
            if nt not in bpy.data.node_groups:
                data_to.node_groups.append(nt)


classes = [
    LicenseConfirmation,
    WM_OT_licenseConfirmation,
    ImportVRM,
    ExportVRM,
    vrm_helper.Bones_rename,
    vrm_helper.Add_VRM_extensions_to_armature,
    vrm_helper.Add_VRM_require_humanbone_custom_property,
    vrm_helper.Add_VRM_defined_humanbone_custom_property,
    vrm_helper.Vroid2VRC_lipsync_from_json_recipe,
    vrm_helper.VRM_VALIDATOR,
    VRM_IMPORTER_PT_controller,
    make_armature.ICYP_OT_MAKE_ARMATURE,
    glsl_drawer.ICYP_OT_Draw_Model,
    glsl_drawer.ICYP_OT_Remove_Draw_Model,
    # detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER,
    # blend_model.ICYP_OT_select_helper,
    # mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES
]


# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.append(make_mesh)
    bpy.app.handlers.load_post.append(add_shaders)


# アドオン無効化時の処理
def unregister():
    bpy.app.handlers.load_post.remove(add_shaders)
    bpy.types.VIEW3D_MT_armature_add.remove(add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.remove(make_mesh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_export)
    bpy.types.TOPBAR_MT_file_export.remove(menu_import)
    errors = []
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            errors.append(
                traceback.format_exc() + f"\nbpy.utils.unregister_class({cls}):"
            )
    if errors:
        raise RuntimeError("\n".join(errors))


if __name__ == "__main__":
    register()
