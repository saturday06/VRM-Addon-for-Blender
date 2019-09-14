"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import bpy
from bpy_extras.io_utils import ImportHelper,ExportHelper
from .importer import vrm_load,model_build
from .misc import VRM_HELPER
from .misc import glb_factory
from .misc import armature_maker
from .misc import mesh_from_bone_envelopes
if bpy.app.build_platform != b'Darwin':
    from .misc import glsl_drawer
import os


bl_info = {
    "name":"VRM_IMPORTER",
    "author": "iCyP",
    "version": (0, 74),
    "blender": (2, 80, 0),
    "location": "File->Import",
    "description": "VRM Importer",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}


class ImportVRM(bpy.types.Operator,ImportHelper):
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob : bpy.props.StringProperty(
        default='*.vrm',
        options={'HIDDEN'}
    )

    is_put_spring_bone_info : bpy.props.BoolProperty(name = "Put Collider Empty")
    import_normal : bpy.props.BoolProperty(name = "Import Normal(has bug)")
    remove_doubles : bpy.props.BoolProperty(name = "Remove doubles")

    def execute(self, context):
        ui_localization = False
        try:
            ui_localization = bpy.context.preferences.view.use_international_fonts
            bpy.context.preferences.view.use_international_fonts = False
        except Exception:
            pass

        fdir = self.filepath
        model_build.Blend_model(context, vrm_load.read_vrm(fdir), self.is_put_spring_bone_info,self.import_normal,self.remove_doubles)
        
        try:
            if ui_localization is not None:
                bpy.context.preferences.view.use_international_fonts = ui_localization
        except Exception:
            pass
            
        return {'FINISHED'}


def menu_import(self, context):
    op = self.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")
    op.is_put_spring_bone_info = True
    op.import_normal = True
    op.remove_doubles = False

class ExportVRM(bpy.types.Operator,ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob : bpy.props.StringProperty(
        default='*.vrm',
        options={'HIDDEN'}
    )

    def execute(self,context):
        fdir = self.filepath
        bin =  glb_factory.Glb_obj().convert_bpy2glb()
        with open(fdir,"wb") as f:
            f.write(bin)
        return {'FINISHED'}


def menu_export(self, context):
    op = self.layout.operator(ExportVRM.bl_idname, text="VRM (.vrm)")

def add_armature(self, context):
    op = self.layout.operator(armature_maker.ICYP_OT_MAKE_ARAMATURE.bl_idname, text="VRM humanoid")

def make_mesh(self, context):
    op = self.layout.operator(mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES.bl_idname, text="Mesh from selected armature",icon='PLUGIN')

class VRM_IMPORTER_PT_controller(bpy.types.Panel):
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "vrm import helper"
    #どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM HELPER"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        self.layout.label(text="If you select armature in object mode")
        self.layout.label(text="armature renamer is shown")
        self.layout.label(text="If you in MESH EDIT")
        self.layout.label(text="symmetry button is shown")
        self.layout.label(text="*Symmetry is in default blender function")
        if context.mode == "OBJECT":
            if context.active_object is not None:
                self.layout.operator(VRM_HELPER.VRM_VALIDATOR.bl_idname)
                if bpy.app.build_platform != b'Darwin':
                    self.layout.operator(glsl_drawer.ICYP_OT_Draw_Model.bl_idname)
                    self.layout.operator(glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname)
                if context.active_object.type == 'ARMATURE':
                    self.layout.label(icon ="ERROR" ,text="EXPERIMENTAL!!!")
                    self.layout.operator(VRM_HELPER.Bones_rename.bl_idname)
                if context.active_object.type =="MESH":
                    self.layout.label(icon="ERROR",text="EXPERIMENTAL！！！")
                    self.layout.operator(VRM_HELPER.Vroid2VRC_ripsync_from_json_recipe.bl_idname)
        if context.mode == "EDIT_MESH":
            self.layout.operator(bpy.ops.mesh.symmetry_snap.idname_py())

from bpy.app.handlers import persistent
@persistent
def add_shaders(self):
    filedir = os.path.join(os.path.dirname(__file__),"resources","material_node_groups.blend")
    with bpy.data.libraries.load(filedir, link=False) as (data_from, data_to):
        for nt in data_from.node_groups:
            if nt not in bpy.data.node_groups:
                data_to.node_groups.append(nt)


classes = [
    ImportVRM,
    ExportVRM,
    VRM_HELPER.Bones_rename,
    VRM_HELPER.Vroid2VRC_ripsync_from_json_recipe,
    VRM_HELPER.VRM_VALIDATOR,
    VRM_IMPORTER_PT_controller,
    armature_maker.ICYP_OT_MAKE_ARAMATURE,
    model_build.ICYP_OT_select_helper,
    mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES
]
if bpy.app.build_platform != b'Darwin':
    classes.extend([
        glsl_drawer.ICYP_OT_Draw_Model,
        glsl_drawer.ICYP_OT_Remove_Draw_Model,
        ])

# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(add_armature)
    bpy.types.VIEW3D_MT_mesh_add.append(make_mesh)
    bpy.app.handlers.load_post.append(add_shaders) 
    

# アドオン無効化時の処理
def unregister():
    bpy.app.handlers.load_post.remove(add_shaders)
    bpy.types.VIEW3D_MT_armature_add.remove(add_armature)
    bpy.types.VIEW3D_MT_mesh_add.remove(make_mesh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_export)
    bpy.types.TOPBAR_MT_file_export.remove(menu_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if "__main__" == __name__:
    register()

