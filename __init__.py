"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.app.handlers import persistent
from .importer import vrm_load, blend_model
from .misc import vrm_helper
from .misc import glb_factory
from .misc import make_armature
from .misc import detail_mesh_maker
from .misc import mesh_from_bone_envelopes
from .misc import version
from . import vrm_types

if bpy.app.build_platform != b"Darwin":
    from .misc import glsl_drawer
import os

bl_info = {
    "name": "VRM_IMPORTER",
    "author": "saturday06, iCyP",
    # I'd like to use version.version(). But that is not allowed.
    "version": (0, 90, 0),
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


class ImportVRM(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    make_new_texture_folder: bpy.props.BoolProperty(
        name="make new texture folder (limit:10)"  # noqa: F722
    )
    is_put_spring_bone_info: bpy.props.BoolProperty(
        name="Put Collider Empty"  # noqa: F722
    )
    import_normal: bpy.props.BoolProperty(name="Import Normal")  # noqa: F722
    remove_doubles: bpy.props.BoolProperty(name="Remove doubles")  # noqa: F722
    set_bone_roll: bpy.props.BoolProperty(name="Set bone roll")  # noqa: F722
    use_simple_principled_material: bpy.props.BoolProperty(
        name="use simple principled material"  # noqa: F722
    )
    use_in_blender: bpy.props.BoolProperty(
        name="NOTHING TO DO in CURRENT use in blender"  # noqa: F722
    )

    def execute(self, context):
        has_ui_localization = bpy.app.version < (2, 83)
        if has_ui_localization:
            ui_localization = bpy.context.preferences.view.use_international_fonts

        blend_model.BlendModel(context, vrm_load.read_vrm(self.filepath, self), self)

        if has_ui_localization and ui_localization:
            bpy.context.preferences.view.use_international_fonts = ui_localization

        return {"FINISHED"}


def menu_import(self, context):
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
    filter_glob: bpy.props.StringProperty(
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    # VRM_version : bpy.props.EnumProperty(name="VRM version" ,items=(("0.0","0.0",""),("1.0","1.0","")))

    def execute(self, context):
        try:
            glb_obj = glb_factory.GlbObj()
        except glb_factory.GlbObj.ValidationError:
            return {"CANCELLED"}
        # vrm_bin =  glb_obj().convert_bpy2glb(self.VRM_version)
        vrm_bin = glb_obj.convert_bpy2glb("0.0")
        with open(self.filepath, "wb") as f:
            f.write(vrm_bin)
        return {"FINISHED"}


def menu_export(self, context):
    self.layout.operator(ExportVRM.bl_idname, text="VRM (.vrm)")


def add_armature(self, context):
    self.layout.operator(
        make_armature.ICYP_OT_MAKE_ARMATURE.bl_idname, text="VRM humanoid"
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
    bl_label = "vrm import helper"
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
            abox = self.layout.row(align=False).box()
            abox.label(text="Armature Help")
            abox.operator(vrm_helper.Add_VRM_extensions_to_armature.bl_idname)
            self.layout.separator()

            reqbox = abox.box()
            reqrow = reqbox.row()
            reqrow.label(text="VRM Required Bones")
            for req in vrm_types.HumanBones.requires:
                if req in context.active_object.data:
                    reqbox.prop_search(
                        context.active_object.data,
                        f'["{req}"]',
                        context.active_object.data,
                        "bones",
                        text=req,
                    )
                else:
                    reqbox.operator(
                        vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                        text=f"Add {req} property",
                    )
            defbox = abox.box()
            defbox.label(text="VRM Optional Bones")
            for defs in vrm_types.HumanBones.defines:
                if defs in context.active_object.data:
                    defbox.prop_search(
                        context.active_object.data,
                        f'["{defs}"]',
                        context.active_object.data,
                        "bones",
                        text=defs,
                    )
                else:
                    defbox.operator(
                        vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                        text=f"Add {defs} property",
                    )

            abox.label(icon="ERROR", text="EXPERIMENTAL!!!")
            abox.operator(vrm_helper.Bones_rename.bl_idname)
            return

        # endregion helper

        # region draw_main
        self.layout.label(text="If you select armature in object mode")
        self.layout.label(text="armature renamer is shown")
        self.layout.label(text="If you in MESH EDIT")
        self.layout.label(text="symmetry button is shown")
        self.layout.label(text="*Symmetry is in default blender function")
        if context.mode == "OBJECT":
            if context.active_object is not None:
                self.layout.operator(vrm_helper.VRM_VALIDATOR.bl_idname)
                if bpy.app.build_platform != b"Darwin":
                    mbox = self.layout.box()
                    mbox.label(text="MToon preview")
                    mbox.operator(glsl_drawer.ICYP_OT_Draw_Model.bl_idname)
                    mbox.operator(glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname)
                if context.active_object.type == "ARMATURE":
                    armature_ui()
                if context.active_object.type == "MESH":
                    self.layout.label(icon="ERROR", text="EXPERIMENTAL!!!")
                    self.layout.operator(
                        vrm_helper.Vroid2VRC_ripsync_from_json_recipe.bl_idname
                    )

        if context.mode == "EDIT_MESH":
            self.layout.operator(bpy.ops.mesh.symmetry_snap.idname_py())

        if context.mode == "POSE":
            if context.active_object.type == "ARMATURE":
                armature_ui()
        return
        # endregion draw_main


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
    ImportVRM,
    ExportVRM,
    vrm_helper.Bones_rename,
    vrm_helper.Add_VRM_extensions_to_armature,
    vrm_helper.Add_VRM_require_humanbone_custom_property,
    vrm_helper.Add_VRM_defined_humanbone_custom_property,
    vrm_helper.Vroid2VRC_ripsync_from_json_recipe,
    vrm_helper.VRM_VALIDATOR,
    VRM_IMPORTER_PT_controller,
    make_armature.ICYP_OT_MAKE_ARMATURE,
    # detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER,
    # blend_model.ICYP_OT_select_helper,
    # mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES
]
if bpy.app.build_platform != b"Darwin":
    classes.extend(
        [glsl_drawer.ICYP_OT_Draw_Model, glsl_drawer.ICYP_OT_Remove_Draw_Model]
    )


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
    for cls in classes:
        bpy.utils.unregister_class(cls)


if "__main__" == __name__:
    register()
