"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Callable

import bpy
from bpy.app.handlers import persistent

from .common import preferences, shader
from .common.logging import get_logger
from .common.version import addon_version, trigger_clear_addon_version_cache
from .editor import (
    extension,
    make_armature,
    migration,
    ops,
    panel,
    property_group,
    validation,
)
from .editor.mtoon0 import glsl_drawer
from .editor.mtoon1 import handler as mtoon1_handler
from .editor.mtoon1 import ops as mtoon1_ops
from .editor.mtoon1 import panel as mtoon1_panel
from .editor.mtoon1 import property_group as mtoon1_property_group
from .editor.node_constraint1 import panel as node_constraint1_panel
from .editor.node_constraint1 import property_group as node_constraint1_property_group
from .editor.spring_bone1 import handler as spring_bone1_handler
from .editor.spring_bone1 import ops as spring_bone1_ops
from .editor.spring_bone1 import panel as spring_bone1_panel
from .editor.spring_bone1 import property_group as spring_bone1_property_group
from .editor.vrm0 import ops as vrm0_ops
from .editor.vrm0 import panel as vrm0_panel
from .editor.vrm0 import property_group as vrm0_property_group
from .editor.vrm1 import ops as vrm1_ops
from .editor.vrm1 import panel as vrm1_panel
from .editor.vrm1 import property_group as vrm1_property_group
from .exporter import export_scene
from .external import io_scene_gltf2_support
from .importer import import_scene
from .locale.translation_dictionary import translation_dictionary

logger = get_logger(__name__)

if not persistent:  # for fake-bpy-modules

    def persistent(_func: Callable[[object], None]) -> Callable[[object], None]:
        raise NotImplementedError


@persistent  # type: ignore[misc]
def load_post(_dummy: object) -> None:
    shader.add_shaders()
    migration.migrate_all_objects()
    migration.setup_subscription(load_post=True)


@persistent  # type: ignore[misc]
def depsgraph_update_pre_once(_dummy: object) -> None:
    # register時もload_postと同様の初期化を行いたい。しかし、registerに直接書くと
    # Blender起動直後のコンテキストではエラーになってしまう。そのためdepsgraph_update_preを使う。
    if depsgraph_update_pre_once not in bpy.app.handlers.depsgraph_update_pre:
        return
    bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_update_pre_once)
    shader.add_shaders()
    migration.migrate_all_objects()
    migration.setup_subscription(load_post=False)


@persistent  # type: ignore[misc]
def depsgraph_update_pre(_dummy: object) -> None:
    trigger_clear_addon_version_cache()


@persistent  # type: ignore[misc]
def save_pre(_dummy: object) -> None:
    # 保存の際にtimersに登録したコールバックがもし起動しても内部データを変更しないようにする
    depsgraph_update_pre_once(None)
    migration.migrate_all_objects()
    extension.update_internal_cache(bpy.context)


classes = [
    io_scene_gltf2_support.WM_OT_vrm_io_scene_gltf2_disabled_warning,
    property_group.StringPropertyGroup,
    property_group.FloatPropertyGroup,
    property_group.BonePropertyGroup,
    property_group.MeshObjectPropertyGroup,
    vrm0_property_group.Vrm0MaterialValueBindPropertyGroup,
    vrm0_property_group.Vrm0BlendShapeBindPropertyGroup,
    vrm0_property_group.Vrm0BlendShapeGroupPropertyGroup,
    vrm0_property_group.Vrm0BlendShapeMasterPropertyGroup,
    vrm0_property_group.Vrm0MeshAnnotationPropertyGroup,
    vrm0_property_group.Vrm0DegreeMapPropertyGroup,
    vrm0_property_group.Vrm0FirstPersonPropertyGroup,
    vrm0_property_group.Vrm0HumanoidBonePropertyGroup,
    vrm0_property_group.Vrm0HumanoidPropertyGroup,
    vrm0_property_group.Vrm0MetaPropertyGroup,
    vrm0_property_group.Vrm0SecondaryAnimationColliderPropertyGroup,
    vrm0_property_group.Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    vrm0_property_group.Vrm0SecondaryAnimationGroupPropertyGroup,
    vrm0_property_group.Vrm0SecondaryAnimationPropertyGroup,
    vrm0_property_group.Vrm0PropertyGroup,
    # vrm0_gizmo_group.Vrm0FirstPersonBoneOffsetGizmoGroup,
    vrm1_property_group.Vrm1HumanBonePropertyGroup,
    vrm1_property_group.Vrm1HumanBonesPropertyGroup,
    vrm1_property_group.Vrm1HumanoidPropertyGroup,
    vrm1_property_group.Vrm1LookAtRangeMapPropertyGroup,
    vrm1_property_group.Vrm1LookAtPropertyGroup,
    vrm1_property_group.Vrm1MeshAnnotationPropertyGroup,
    vrm1_property_group.Vrm1FirstPersonPropertyGroup,
    vrm1_property_group.Vrm1MorphTargetBindPropertyGroup,
    vrm1_property_group.Vrm1MaterialColorBindPropertyGroup,
    vrm1_property_group.Vrm1TextureTransformBindPropertyGroup,
    vrm1_property_group.Vrm1ExpressionPropertyGroup,
    vrm1_property_group.Vrm1CustomExpressionPropertyGroup,
    vrm1_property_group.Vrm1ExpressionsPropertyGroup,
    vrm1_property_group.Vrm1MetaPropertyGroup,
    vrm1_property_group.Vrm1PropertyGroup,
    node_constraint1_property_group.NodeConstraint1NodeConstraintPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapeSpherePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapeCapsulePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderReferencePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderGroupPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderGroupReferencePropertyGroup,
    spring_bone1_property_group.SpringBone1JointStatePropertyGroup,
    spring_bone1_property_group.SpringBone1JointPropertyGroup,
    spring_bone1_property_group.SpringBone1SpringPropertyGroup,
    spring_bone1_property_group.SpringBone1SpringBonePropertyGroup,
    mtoon1_property_group.MaterialTraceablePropertyGroup,
    mtoon1_property_group.Mtoon1SamplerPropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1NormalSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1KhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1NormalKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1TexturePropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorTexturePropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1NormalTexturePropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftTexturePropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveTexturePropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1MatcapTexturePropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskTexturePropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1NormalTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1NormalTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskTextureInfoPropertyGroup,
    mtoon1_property_group.Mtoon1PbrMetallicRoughnessPropertyGroup,
    mtoon1_property_group.Mtoon1VrmcMaterialsMtoonPropertyGroup,
    mtoon1_property_group.Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup,
    mtoon1_property_group.Mtoon1MaterialExtensionsPropertyGroup,
    mtoon1_property_group.Mtoon1MaterialPropertyGroup,
    mtoon1_panel.VRM_PT_vrm_material_property,
    panel.VRM_PT_current_selected_armature,
    panel.VRM_PT_controller_unsupported_blender_version_warning,
    panel.VRM_PT_controller,
    panel.VRM_PT_vrm_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_meta_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_meta_ui,
    vrm0_panel.VRM_PT_vrm0_humanoid_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_humanoid_ui,
    vrm0_panel.VRM_PT_vrm0_blend_shape_master_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_blend_shape_master_ui,
    vrm0_panel.VRM_PT_vrm0_first_person_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_first_person_ui,
    vrm0_panel.VRM_PT_vrm0_secondary_animation_armature_object_property,
    vrm0_panel.VRM_PT_vrm0_secondary_animation_ui,
    vrm1_panel.VRM_PT_vrm1_meta_armature_object_property,
    vrm1_panel.VRM_PT_vrm1_meta_ui,
    vrm1_panel.VRM_PT_vrm1_humanoid_armature_object_property,
    vrm1_panel.VRM_PT_vrm1_humanoid_ui,
    vrm1_panel.VRM_PT_vrm1_first_person_armature_object_property,
    vrm1_panel.VRM_PT_vrm1_first_person_ui,
    vrm1_panel.VRM_PT_vrm1_look_at_armature_object_property,
    vrm1_panel.VRM_PT_vrm1_look_at_ui,
    vrm1_panel.VRM_PT_vrm1_expressions_armature_object_property,
    vrm1_panel.VRM_PT_vrm1_expressions_ui,
    node_constraint1_panel.VRM_PT_node_constraint1_armature_object_property,
    node_constraint1_panel.VRM_PT_node_constraint1_ui,
    spring_bone1_panel.VRM_PT_spring_bone1_armature_object_property,
    spring_bone1_panel.VRM_PT_spring_bone1_ui,
    spring_bone1_panel.VRM_PT_spring_bone1_collider_property,
    vrm0_ops.VRM_OT_add_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_remove_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_add_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_remove_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_add_vrm0_material_value_bind_target_value,
    vrm0_ops.VRM_OT_remove_vrm0_material_value_bind_target_value,
    vrm0_ops.VRM_OT_add_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_remove_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_add_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_remove_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_assign_vrm0_humanoid_human_bones_automatically,
    vrm1_ops.VRM_OT_add_vrm1_meta_author,
    vrm1_ops.VRM_OT_remove_vrm1_meta_author,
    vrm1_ops.VRM_OT_add_vrm1_meta_reference,
    vrm1_ops.VRM_OT_remove_vrm1_meta_reference,
    vrm1_ops.VRM_OT_add_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_remove_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_add_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_add_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_add_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_add_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_remove_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_add_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_add_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_add_spring_bone1_spring_joint,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_spring_joint,
    mtoon1_ops.VRM_OT_convert_material_to_mtoon1,
    mtoon1_ops.VRM_OT_convert_mtoon1_to_bsdf_principled,
    mtoon1_ops.VRM_OT_reset_mtoon1_material_shader_node_tree,
    mtoon1_ops.VRM_OT_import_mtoon1_texture_image_file,
    mtoon1_ops.VRM_OT_refresh_mtoon1_outline,
    # editor.detail_mesh_maker.ICYP_OT_detail_mesh_maker,
    glsl_drawer.ICYP_OT_draw_model,
    glsl_drawer.ICYP_OT_remove_draw_model,
    make_armature.ICYP_OT_make_armature,
    # editor.mesh_from_bone_envelopes.ICYP_OT_make_mesh_from_bone_envelopes,
    ops.VRM_OT_add_human_bone_custom_property,
    ops.VRM_OT_add_defined_human_bone_custom_property,  # deprecated
    ops.VRM_OT_add_extensions_to_armature,
    ops.VRM_OT_add_required_human_bone_custom_property,  # deprecated
    ops.VRM_OT_simplify_vroid_bones,
    ops.VRM_OT_vroid2vrc_lipsync_from_json_recipe,
    ops.VRM_OT_open_url_in_web_browser,
    ops.VRM_OT_save_human_bone_mappings,
    ops.VRM_OT_load_human_bone_mappings,
    validation.VrmValidationError,
    validation.WM_OT_vrm_validator,
    export_scene.VRM_PT_export_error_messages,
    export_scene.WM_OT_vrm_export_human_bones_assignment,
    export_scene.WM_OT_vrm_export_confirmation,
    export_scene.WM_OT_vrm_export_armature_selection,
    export_scene.EXPORT_SCENE_OT_vrm,
    import_scene.LicenseConfirmation,
    import_scene.WM_OT_vrm_license_confirmation,
    import_scene.IMPORT_SCENE_OT_vrm,
    import_scene.VRM_PT_import_unsupported_blender_version_warning,
    # importer.blend_model.ICYP_OT_select_helper,
    preferences.VrmAddonPreferences,
    extension.VrmAddonArmatureExtensionPropertyGroup,
    extension.VrmAddonBoneExtensionPropertyGroup,
    extension.VrmAddonSceneExtensionPropertyGroup,
    extension.VrmAddonMaterialExtensionPropertyGroup,
    extension.VrmAddonObjectExtensionPropertyGroup,
]


def register(init_addon_version: object) -> None:
    # Sanity check. Because a addon_version() implementation is very acrobatic
    # and it can break easily.
    if init_addon_version != addon_version():
        raise AssertionError(
            f"Sanity error: version mismatch: {init_addon_version} != {addon_version()}"
        )

    bpy.app.translations.register(
        preferences.addon_package_name,
        translation_dictionary,
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Material.vrm_addon_extension = bpy.props.PointerProperty(
        type=extension.VrmAddonMaterialExtensionPropertyGroup
    )

    bpy.types.Scene.vrm_addon_extension = bpy.props.PointerProperty(
        type=extension.VrmAddonSceneExtensionPropertyGroup
    )

    bpy.types.Bone.vrm_addon_extension = bpy.props.PointerProperty(
        type=extension.VrmAddonBoneExtensionPropertyGroup
    )

    bpy.types.Armature.vrm_addon_extension = bpy.props.PointerProperty(
        type=extension.VrmAddonArmatureExtensionPropertyGroup
    )

    bpy.types.Object.vrm_addon_extension = bpy.props.PointerProperty(
        type=extension.VrmAddonObjectExtensionPropertyGroup
    )

    bpy.types.TOPBAR_MT_file_import.append(import_scene.menu_import)
    bpy.types.TOPBAR_MT_file_export.append(export_scene.menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(panel.add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.append(panel.make_mesh)

    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.depsgraph_update_pre.append(depsgraph_update_pre_once)
    bpy.app.handlers.depsgraph_update_pre.append(depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.append(mtoon1_handler.depsgraph_update_pre)
    bpy.app.handlers.save_pre.append(save_pre)
    bpy.app.handlers.save_pre.append(mtoon1_handler.save_pre)
    bpy.app.handlers.frame_change_pre.append(spring_bone1_handler.frame_change_pre)
    bpy.app.handlers.depsgraph_update_pre.append(
        spring_bone1_handler.depsgraph_update_pre
    )

    io_scene_gltf2_support.init_extras_export()


def unregister() -> None:
    migration.teardown_subscription()  # migration.setup_subscription()はload_postで呼ばれる

    bpy.app.handlers.depsgraph_update_pre.remove(
        spring_bone1_handler.depsgraph_update_pre
    )
    bpy.app.handlers.frame_change_pre.remove(spring_bone1_handler.frame_change_pre)
    bpy.app.handlers.save_pre.remove(mtoon1_handler.save_pre)
    bpy.app.handlers.save_pre.remove(save_pre)
    bpy.app.handlers.depsgraph_update_pre.remove(mtoon1_handler.depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_update_pre)
    if depsgraph_update_pre_once in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_update_pre_once)
    bpy.app.handlers.load_post.remove(load_post)

    # bpy.types.VIEW3D_MT_mesh_add.remove(panel.make_mesh)
    bpy.types.VIEW3D_MT_armature_add.remove(panel.add_armature)
    bpy.types.TOPBAR_MT_file_export.remove(export_scene.menu_export)
    bpy.types.TOPBAR_MT_file_import.remove(import_scene.menu_import)

    if hasattr(bpy.types.Object, "vrm_addon_extension"):
        del bpy.types.Object.vrm_addon_extension

    if hasattr(bpy.types.Armature, "vrm_addon_extension"):
        del bpy.types.Armature.vrm_addon_extension

    if hasattr(bpy.types.Bone, "vrm_addon_extension"):
        del bpy.types.Bone.vrm_addon_extension

    if hasattr(bpy.types.Scene, "vrm_addon_extension"):
        del bpy.types.Scene.vrm_addon_extension

    if hasattr(bpy.types.Material, "vrm_addon_extension"):
        del bpy.types.Material.vrm_addon_extension

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            logger.exception(f"Failed to Unregister {cls}")

    bpy.app.translations.unregister(preferences.addon_package_name)
