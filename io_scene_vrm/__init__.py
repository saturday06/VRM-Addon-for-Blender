"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Any, Set, cast

import bpy
from bpy.app.handlers import persistent

from . import editor, exporter, importer, locale
from .common import preferences, shader, version


class WM_OT_gltf2_addon_disabled_warning(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "glTF 2.0 add-on is disabled"
    bl_idname = "wm.gltf2_addon_disabled_warning"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=500)
        )

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.label(
            text='Official add-on "glTF 2.0 format" is required. Please enable it.'
        )


if persistent:  # for fake-bpy-modules

    @persistent  # type: ignore[misc]
    def add_shaders(_dummy: Any) -> None:
        shader.add_shaders()


classes = [
    WM_OT_gltf2_addon_disabled_warning,
    editor.ObjectPropertyGroup,
    editor.StringPropertyGroup,
    editor.FloatPropertyGroup,
    editor.BonePropertyGroup,
    editor.MeshPropertyGroup,
    editor.Vrm0MaterialValueBindPropertyGroup,
    editor.Vrm0BlendShapeBindPropertyGroup,
    editor.Vrm0BlendShapeGroupPropertyGroup,
    editor.Vrm0BlendShapeMasterPropertyGroup,
    editor.Vrm0MeshAnnotationPropertyGroup,
    editor.Vrm0DegreeMapPropertyGroup,
    editor.Vrm0FirstPersonPropertyGroup,
    editor.Vrm0HumanoidBonePropertyGroup,
    editor.Vrm0HumanoidPropertyGroup,
    editor.Vrm0MetaPropertyGroup,
    editor.Vrm0SecondaryAnimationCollider,
    editor.Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    editor.Vrm0SecondaryAnimationGroupPropertyGroup,
    editor.Vrm0SecondaryAnimationPropertyGroup,
    editor.VRM_PT_current_selected_armature,
    editor.VRM_PT_controller,
    editor.VRM_PT_vrm_armature_object_property,
    editor.VRM_PT_vrm0_meta_armature_object_property,
    editor.VRM_PT_vrm0_meta_ui,
    editor.VRM_PT_vrm0_humanoid_armature_object_property,
    editor.VRM_PT_vrm0_humanoid_ui,
    editor.VRM_PT_vrm0_blend_shape_master_armature_object_property,
    editor.VRM_PT_vrm0_blend_shape_master_ui,
    editor.VRM_PT_vrm0_first_person_armature_object_property,
    editor.VRM_PT_vrm0_first_person_ui,
    editor.VRM_PT_vrm0_secondary_animation_armature_object_property,
    editor.VRM_PT_vrm0_secondary_animation_ui,
    editor.VRM_OT_add_vrm0_first_person_mesh_annotation,
    editor.VRM_OT_remove_vrm0_first_person_mesh_annotation,
    editor.VRM_OT_add_vrm0_material_value_bind,
    editor.VRM_OT_remove_vrm0_material_value_bind,
    editor.VRM_OT_add_vrm0_material_value_bind_target_value,
    editor.VRM_OT_remove_vrm0_material_value_bind_target_value,
    editor.VRM_OT_add_vrm0_blend_shape_bind,
    editor.VRM_OT_remove_vrm0_blend_shape_bind,
    editor.VRM_OT_add_vrm0_secondary_animation_collider_group_collider,
    editor.VRM_OT_remove_vrm0_secondary_animation_collider_group_collider,
    editor.VRM_OT_add_vrm0_secondary_animation_group_bone,
    editor.VRM_OT_remove_vrm0_secondary_animation_group_bone,
    editor.VRM_OT_add_vrm0_secondary_animation_group_collider_group,
    editor.VRM_OT_remove_vrm0_secondary_animation_group_collider_group,
    editor.VRM_OT_add_vrm0_blend_shape_group,
    editor.VRM_OT_remove_vrm0_blend_shape_group,
    editor.VRM_OT_add_vrm0_secondary_animation_group,
    editor.VRM_OT_remove_vrm0_secondary_animation_group,
    editor.VRM_OT_add_vrm0_secondary_animation_collider_group,
    editor.VRM_OT_remove_vrm0_secondary_animation_collider_group,
    # editor.detail_mesh_maker.ICYP_OT_detail_mesh_maker,
    editor.glsl_drawer.ICYP_OT_draw_model,
    editor.glsl_drawer.ICYP_OT_remove_draw_model,
    editor.make_armature.ICYP_OT_make_armature,
    # editor.mesh_from_bone_envelopes.ICYP_OT_make_mesh_from_bone_envelopes,
    editor.helper.VRM_OT_add_human_bone_custom_property,
    editor.helper.VRM_OT_add_defined_human_bone_custom_property,  # deprecated
    editor.helper.VRM_OT_add_extensions_to_armature,
    editor.helper.VRM_OT_add_required_human_bone_custom_property,  # deprecated
    editor.helper.VRM_OT_rename_bones,
    editor.helper.VRM_OT_vroid2vrc_lipsync_from_json_recipe,
    editor.helper.VRM_OT_save_human_bone_mappings,
    editor.helper.VRM_OT_load_human_bone_mappings,
    exporter.validation.VrmValidationError,
    exporter.validation.WM_OT_vrm_validator,
    exporter.EXPORT_SCENE_OT_vrm,
    exporter.VRM_PT_export_error_messages,
    importer.IMPORT_SCENE_OT_vrm,
    importer.LicenseConfirmation,
    importer.WM_OT_license_confirmation,
    # importer.blend_model.ICYP_OT_select_helper,
    preferences.VrmAddonPreferences,
    editor.Vrm0PropertyGroup,
    editor.VrmAddonArmatureExtensionPropertyGroup,
]


# アドオン有効化時の処理
def register(init_version: Any) -> None:
    # Sanity check
    if init_version != version.version():
        raise Exception(
            f"Sanity error: version mismatch: {init_version} != {version.version()}"
        )

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(importer.menu_import)
    bpy.types.TOPBAR_MT_file_export.append(exporter.menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(editor.add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.append(editor.make_mesh)
    bpy.app.handlers.load_post.append(add_shaders)
    bpy.app.translations.register(
        preferences.addon_package_name, locale.translation_dictionary
    )
    bpy.types.Armature.vrm_addon_extension = bpy.props.PointerProperty(
        type=editor.VrmAddonArmatureExtensionPropertyGroup
    )


# アドオン無効化時の処理
def unregister() -> None:
    bpy.app.translations.unregister(preferences.addon_package_name)
    bpy.app.handlers.load_post.remove(add_shaders)
    bpy.types.VIEW3D_MT_armature_add.remove(editor.add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.remove(editor.make_mesh)
    bpy.types.TOPBAR_MT_file_import.remove(importer.menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(exporter.menu_export)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Armature, "vrm_addon_extension"):
        del bpy.types.Armature.vrm_addon_extension
    if hasattr(bpy.types.Bone, "vrm_addon_extension"):
        del bpy.types.Bone.vrm_addon_extension
    if hasattr(bpy.types.ShapeKey, "vrm_addon_extension"):
        del bpy.types.ShapeKey.vrm_addon_extension
