"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Any, Set, cast

import bpy
from bpy.app.handlers import persistent

from . import editor, exporter, importer, shader, version
from .editor import glsl_drawer, make_armature, vrm_helper
from .exporter import validation
from .lang import translation_dictionary
from .preferences import (
    VrmAddonPreferences,
    addon_package_name,
    use_experimental_vrm_component_ui,
)


class WM_OT_gltf2AddonDisabledWarning(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "glTF 2.0 add-on is disabled"
    bl_idname = "wm.gltf2_addon_disabled_warning"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=500)
        )

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(
            text='Official add-on "glTF 2.0 format" is required. Please enable it.'
        )


if persistent:  # for fake-bpy-modules

    @persistent  # type: ignore[misc]
    def add_shaders(self: Any) -> None:
        shader.add_shaders(self)


classes = [
    VrmAddonPreferences,
    importer.LicenseConfirmation,
    importer.WM_OT_licenseConfirmation,
    WM_OT_gltf2AddonDisabledWarning,
    vrm_helper.Bones_rename,
    vrm_helper.Add_VRM_extensions_to_armature,
    vrm_helper.Add_VRM_require_humanbone_custom_property,
    vrm_helper.Add_VRM_defined_humanbone_custom_property,
    vrm_helper.Vroid2VRC_lipsync_from_json_recipe,
    validation.VrmValidationError,
    validation.WM_OT_vrmValidator,
    importer.ImportVRM,
    exporter.ExportVRM,
    exporter.VRM_IMPORTER_PT_export_error_messages,
    editor.VRM_IMPORTER_PT_controller,
    make_armature.ICYP_OT_MAKE_ARMATURE,
    glsl_drawer.ICYP_OT_Draw_Model,
    glsl_drawer.ICYP_OT_Remove_Draw_Model,
    # detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER,
    # blend_model.ICYP_OT_select_helper,
    # mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES
    editor.HUMANOID_PARAMS,
    editor.LOOKAT_CURVE,
    editor.MESH_ANNOTATION,
    editor.FIRSTPERSON_PARAMS,
    editor.BLENDSHAPE_BIND,
    editor.BLENDSHAPE_MATERIAL_BIND,
    editor.BLENDSHAPE_GROUP,
    editor.COLLIDER_GROUP,
    editor.BONE_GROUP,
    editor.SPRING_BONE_GROUP,
    editor.METAS,
    editor.REQUIRED_METAS,
]

experimental_vrm_component_ui_classes = [
    editor.VRM_IMPORTER_PT_armature_controller,
    editor.VRMProps,
    editor.VRM_IMPORTER_PT_vrm_humanoid_params,
    editor.VRM_IMPORTER_PT_vrm_firstPerson_params,
    editor.VRM_IMPORTER_PT_vrm_blendshape_group,
    editor.VRM_IMPORTER_PT_vrm_spring_bone,
    editor.VRM_IMPORTER_PT_vrm_metas,
]


def set_use_experimental_vrm_component_ui(enable: bool) -> None:
    has_props = hasattr(bpy.types.Object, "vrm_props")
    if enable and not has_props:
        for cls in experimental_vrm_component_ui_classes:
            bpy.utils.register_class(cls)
        bpy.types.Object.vrm_props = bpy.props.PointerProperty(type=editor.VRMProps)
    elif not enable and has_props:
        del bpy.types.Object.vrm_props
        for cls in experimental_vrm_component_ui_classes:
            bpy.utils.unregister_class(cls)


# アドオン有効化時の処理
def register(init_version: Any) -> None:
    # Sanity check
    if init_version != version.version():
        raise Exception(f"Version mismatch: {init_version} != {version.version()}")

    VrmAddonPreferences.set_use_experimental_vrm_component_ui_callback = (
        set_use_experimental_vrm_component_ui
    )
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(importer.menu_import)
    bpy.types.TOPBAR_MT_file_export.append(exporter.menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(editor.add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.append(editor.make_mesh)
    bpy.app.handlers.load_post.append(add_shaders)
    bpy.app.translations.register(addon_package_name, translation_dictionary)

    set_use_experimental_vrm_component_ui(
        use_experimental_vrm_component_ui(bpy.context)
    )


# アドオン無効化時の処理
def unregister() -> None:
    bpy.app.translations.unregister(addon_package_name)
    bpy.app.handlers.load_post.remove(add_shaders)
    bpy.types.VIEW3D_MT_armature_add.remove(editor.add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.remove(editor.make_mesh)
    bpy.types.TOPBAR_MT_file_import.remove(importer.menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(exporter.menu_export)
    for cls in classes:
        bpy.utils.unregister_class(cls)
