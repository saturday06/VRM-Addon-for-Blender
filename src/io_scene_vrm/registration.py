# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

from typing import Union

import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty
from bpy.types import (
    AddonPreferences,
    Armature,
    Bone,
    Header,
    KeyingSetInfo,
    Material,
    Menu,
    NodeTree,
    Object,
    Operator,
    Panel,
    PropertyGroup,
    RenderEngine,
    Scene,
    TOPBAR_MT_file_export,
    TOPBAR_MT_file_import,
    UIList,
    VIEW3D_MT_armature_add,
)

from .common import preferences, shader
from .common.logger import get_logger
from .common.version import trigger_clear_addon_version_cache
from .editor import (
    extension,
    handler,
    make_armature,
    migration,
    ops,
    panel,
    property_group,
    subscription,
    validation,
)
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
from .editor.spring_bone1 import ui_list as spring_bone1_ui_list
from .editor.vrm0 import handler as vrm0_handler
from .editor.vrm0 import ops as vrm0_ops
from .editor.vrm0 import panel as vrm0_panel
from .editor.vrm0 import property_group as vrm0_property_group
from .editor.vrm0 import ui_list as vrm0_ui_list
from .editor.vrm1 import handler as vrm1_handler
from .editor.vrm1 import ops as vrm1_ops
from .editor.vrm1 import panel as vrm1_panel
from .editor.vrm1 import property_group as vrm1_property_group
from .editor.vrm1 import ui_list as vrm1_ui_list
from .exporter import export_scene
from .external import io_scene_gltf2_support
from .importer import file_handler, import_scene
from .locale.translation_dictionary import translation_dictionary

logger = get_logger(__name__)


def setup(*, load_post: bool) -> None:
    context = bpy.context
    shader.add_shaders(context)
    migration.migrate_all_objects(context, show_progress=True)
    mtoon1_property_group.setup_drivers(context)
    subscription.setup_subscription(load_post=load_post)


@persistent
def load_post(_unused: object) -> None:
    if (
        depsgraph_update_pre_once_if_load_post_is_unavailable
        in bpy.app.handlers.depsgraph_update_pre
    ):
        bpy.app.handlers.depsgraph_update_pre.remove(
            depsgraph_update_pre_once_if_load_post_is_unavailable
        )

    setup(load_post=True)


@persistent
def depsgraph_update_pre_once_if_load_post_is_unavailable(_unused: object) -> None:
    """Execute the same routine as load_post() in depsgraph_update_pre().

    We want to execute the same routine as load_post() when register() is called.
    However, if we execute it directly in register(), an error will occur in the
    context of Blender startup; we can avoid the error by executing it in
    depsgraph_update_pre().
    """
    if (
        depsgraph_update_pre_once_if_load_post_is_unavailable
        not in bpy.app.handlers.depsgraph_update_pre
    ):
        return

    bpy.app.handlers.depsgraph_update_pre.remove(
        depsgraph_update_pre_once_if_load_post_is_unavailable
    )

    setup(load_post=False)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    trigger_clear_addon_version_cache()


@persistent
def save_pre(_unused: object) -> None:
    # Apply pending changes before saving.
    depsgraph_update_pre_once_if_load_post_is_unavailable(None)
    context = bpy.context
    migration.migrate_all_objects(context)
    extension.update_internal_cache(context)


classes: list[
    Union[
        type[Panel],
        type[UIList],
        type[Menu],
        type[Header],
        type[Operator],
        type[KeyingSetInfo],
        type[RenderEngine],
        type[AddonPreferences],
        type[PropertyGroup],
        type["bpy.types.FileHandler"],  # bpy.app.version >= (4, 1, 0)
    ]
] = [
    io_scene_gltf2_support.WM_OT_vrm_io_scene_gltf2_disabled_warning,
    property_group.StringPropertyGroup,
    property_group.FloatPropertyGroup,
    property_group.BonePropertyGroup,
    property_group.MeshObjectPropertyGroup,
    property_group.MaterialPropertyGroup,
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
    vrm0_property_group.Vrm0SecondaryAnimationGroupAnimationStatePropertyGroup,
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
    vrm1_property_group.Vrm1CustomExpressionPropertyGroup,
    vrm1_property_group.Vrm1ExpressionPropertyGroup,
    vrm1_property_group.Vrm1ExpressionsPresetPropertyGroup,
    vrm1_property_group.Vrm1ExpressionsPropertyGroup,
    vrm1_property_group.Vrm1MetaPropertyGroup,
    vrm1_property_group.Vrm1PropertyGroup,
    node_constraint1_property_group.NodeConstraint1NodeConstraintPropertyGroup,
    spring_bone1_property_group.SpringBone1ExtendedColliderShapeSpherePropertyGroup,
    spring_bone1_property_group.SpringBone1ExtendedColliderShapeCapsulePropertyGroup,
    spring_bone1_property_group.SpringBone1ExtendedColliderShapePlanePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapeSpherePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapeCapsulePropertyGroup,
    spring_bone1_property_group.SpringBone1ExtendedColliderShapePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderShapePropertyGroup,
    spring_bone1_property_group.SpringBone1VrmcSpringBoneExtendedColliderPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderExtensionsPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderReferencePropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderGroupPropertyGroup,
    spring_bone1_property_group.SpringBone1ColliderGroupReferencePropertyGroup,
    spring_bone1_property_group.SpringBone1JointAnimationStatePropertyGroup,
    spring_bone1_property_group.SpringBone1JointPropertyGroup,
    spring_bone1_property_group.SpringBone1SpringAnimationStatePropertyGroup,
    spring_bone1_property_group.SpringBone1SpringPropertyGroup,
    spring_bone1_property_group.SpringBone1SpringBonePropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1NormalSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplySamplerPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskSamplerPropertyGroup,
    mtoon1_property_group.Mtoon1SamplerPropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1NormalKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1MatcapKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1KhrTextureTransformPropertyGroup,
    mtoon1_property_group.Mtoon1BaseColorTexturePropertyGroup,
    mtoon1_property_group.Mtoon1ShadeMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1NormalTexturePropertyGroup,
    mtoon1_property_group.Mtoon1ShadingShiftTexturePropertyGroup,
    mtoon1_property_group.Mtoon1EmissiveTexturePropertyGroup,
    mtoon1_property_group.Mtoon1RimMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1MatcapTexturePropertyGroup,
    mtoon1_property_group.Mtoon1OutlineWidthMultiplyTexturePropertyGroup,
    mtoon1_property_group.Mtoon1UvAnimationMaskTexturePropertyGroup,
    mtoon1_property_group.Mtoon1TexturePropertyGroup,
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
    mtoon1_property_group.Mtoon0SamplerPropertyGroup,
    mtoon1_property_group.Mtoon0TexturePropertyGroup,
    mtoon1_property_group.Mtoon0ShadingGradeTexturePropertyGroup,
    mtoon1_property_group.Mtoon0ReceiveShadowTexturePropertyGroup,
    mtoon1_property_group.Mtoon1MaterialPropertyGroup,
    mtoon1_property_group.MaterialTraceablePropertyGroup,
    mtoon1_panel.VRM_PT_vrm_material_property,
    panel.VRM_PT_current_selected_armature,
    panel.VRM_PT_controller_unsupported_blender_version_warning,
    panel.VRM_PT_controller,
    panel.VRM_PT_vrm_armature_object_property,
    vrm0_ui_list.VRM_UL_vrm0_first_person_mesh_annotation,
    vrm0_ui_list.VRM_UL_vrm0_blend_shape_bind,
    vrm0_ui_list.VRM_UL_vrm0_blend_shape_group,
    vrm0_ui_list.VRM_UL_vrm0_material_value_bind,
    vrm0_ui_list.VRM_UL_vrm0_secondary_animation_collider_group,
    vrm0_ui_list.VRM_UL_vrm0_secondary_animation_group,
    vrm0_ui_list.VRM_UL_vrm0_secondary_animation_group_bone,
    vrm0_ui_list.VRM_UL_vrm0_secondary_animation_group_collider_group,
    vrm0_ui_list.VRM_UL_vrm0_secondary_animation_collider_group_collider,
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
    spring_bone1_ui_list.VRM_UL_spring_bone1_collider,
    spring_bone1_ui_list.VRM_UL_spring_bone1_collider_group,
    spring_bone1_ui_list.VRM_UL_spring_bone1_collider_group_collider,
    spring_bone1_ui_list.VRM_UL_spring_bone1_spring,
    spring_bone1_ui_list.VRM_UL_spring_bone1_joint,
    spring_bone1_ui_list.VRM_UL_spring_bone1_spring_collider_group,
    spring_bone1_panel.VRM_PT_spring_bone1_armature_object_property,
    spring_bone1_panel.VRM_PT_spring_bone1_ui,
    spring_bone1_panel.VRM_PT_spring_bone1_collider_property,
    vrm1_ui_list.VRM_UL_vrm1_meta_author,
    vrm1_ui_list.VRM_UL_vrm1_meta_reference,
    vrm1_ui_list.VRM_UL_vrm1_first_person_mesh_annotation,
    vrm1_ui_list.VRM_UL_vrm1_expression,
    vrm1_ui_list.VRM_UL_vrm1_morph_target_bind,
    vrm1_ui_list.VRM_UL_vrm1_material_color_bind,
    vrm1_ui_list.VRM_UL_vrm1_texture_transform_bind,
    vrm0_ops.VRM_OT_add_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_remove_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_move_up_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_move_down_vrm0_first_person_mesh_annotation,
    vrm0_ops.VRM_OT_add_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_remove_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_move_up_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_move_down_vrm0_material_value_bind,
    vrm0_ops.VRM_OT_add_vrm0_material_value_bind_target_value,
    vrm0_ops.VRM_OT_remove_vrm0_material_value_bind_target_value,
    vrm0_ops.VRM_OT_add_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_remove_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_move_up_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_move_down_vrm0_blend_shape_group,
    vrm0_ops.VRM_OT_add_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_remove_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_move_down_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_move_up_vrm0_blend_shape_bind,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_collider_group_collider,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group_bone,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group_collider_group,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_group,
    vrm0_ops.VRM_OT_add_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_remove_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_move_up_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_move_down_vrm0_secondary_animation_collider_group,
    vrm0_ops.VRM_OT_assign_vrm0_humanoid_human_bones_automatically,
    vrm1_ops.VRM_OT_add_vrm1_meta_author,
    vrm1_ops.VRM_OT_remove_vrm1_meta_author,
    vrm1_ops.VRM_OT_move_up_vrm1_meta_author,
    vrm1_ops.VRM_OT_move_down_vrm1_meta_author,
    vrm1_ops.VRM_OT_add_vrm1_meta_reference,
    vrm1_ops.VRM_OT_remove_vrm1_meta_reference,
    vrm1_ops.VRM_OT_move_up_vrm1_meta_reference,
    vrm1_ops.VRM_OT_move_down_vrm1_meta_reference,
    vrm1_ops.VRM_OT_add_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_remove_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_move_up_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_move_down_vrm1_expressions_custom_expression,
    vrm1_ops.VRM_OT_add_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_move_up_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_move_down_vrm1_expression_morph_target_bind,
    vrm1_ops.VRM_OT_add_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_move_up_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_move_down_vrm1_expression_material_color_bind,
    vrm1_ops.VRM_OT_add_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_remove_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_move_up_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_move_down_vrm1_expression_texture_transform_bind,
    vrm1_ops.VRM_OT_add_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_remove_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_move_up_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_move_down_vrm1_first_person_mesh_annotation,
    vrm1_ops.VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
    vrm1_ops.VRM_OT_update_vrm1_expression_ui_list_elements,
    vrm1_ops.VRM_OT_refresh_vrm1_expression_texture_transform_bind_preview,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_collider,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_collider_group,
    spring_bone1_ops.VRM_OT_add_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_collider_group_collider,
    spring_bone1_ops.VRM_OT_add_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_spring,
    spring_bone1_ops.VRM_OT_add_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_spring_collider_group,
    spring_bone1_ops.VRM_OT_add_spring_bone1_joint,
    spring_bone1_ops.VRM_OT_remove_spring_bone1_joint,
    spring_bone1_ops.VRM_OT_move_up_spring_bone1_joint,
    spring_bone1_ops.VRM_OT_move_down_spring_bone1_joint,
    spring_bone1_ops.VRM_OT_reset_spring_bone1_animation_state,
    spring_bone1_ops.VRM_OT_update_spring_bone1_animation,
    mtoon1_ops.VRM_OT_convert_material_to_mtoon1,
    mtoon1_ops.VRM_OT_convert_mtoon1_to_bsdf_principled,
    mtoon1_ops.VRM_OT_reset_mtoon1_material_shader_node_tree,
    mtoon1_ops.VRM_OT_import_mtoon1_texture_image_file,
    mtoon1_ops.VRM_OT_refresh_mtoon1_outline,
    mtoon1_ops.VRM_OT_show_material_blender_4_2_warning,
    make_armature.ICYP_OT_make_armature,
    ops.VRM_OT_simplify_vroid_bones,
    ops.VRM_OT_open_url_in_web_browser,
    ops.VRM_OT_save_human_bone_mappings,
    ops.VRM_OT_load_human_bone_mappings,
    ops.VRM_OT_show_blend_file_compatibility_warning,
    ops.VRM_OT_show_blend_file_addon_compatibility_warning,
    ops.VRM_OT_make_estimated_humanoid_t_pose,
    validation.VrmValidationError,
    validation.WM_OT_vrm_validator,
    export_scene.WM_OT_vrm_export_human_bones_assignment,
    export_scene.WM_OT_vrm_export_confirmation,
    export_scene.WM_OT_vrm_export_armature_selection,
    export_scene.WM_OT_vrma_export_prerequisite,
    export_scene.VRM_PT_export_file_browser_tool_props,
    export_scene.EXPORT_SCENE_OT_vrm,
    export_scene.EXPORT_SCENE_OT_vrma,
    export_scene.VRM_PT_export_vrma_help,
    import_scene.LicenseConfirmation,
    import_scene.WM_OT_vrm_license_confirmation,
    import_scene.WM_OT_vrma_import_prerequisite,
    import_scene.VRM_PT_import_file_browser_tool_props,
    import_scene.IMPORT_SCENE_OT_vrm,
    import_scene.IMPORT_SCENE_OT_vrma,
    import_scene.VRM_PT_import_unsupported_blender_version_warning,
    file_handler.VRM_OT_import_vrm_via_file_handler,
    file_handler.VRM_OT_import_vrma_via_file_handler,
    preferences.VrmAddonPreferences,
    extension.VrmAddonArmatureExtensionPropertyGroup,
    extension.VrmAddonBoneExtensionPropertyGroup,
    extension.VrmAddonSceneExtensionPropertyGroup,
    extension.VrmAddonMaterialExtensionPropertyGroup,
    extension.VrmAddonObjectExtensionPropertyGroup,
    extension.VrmAddonNodeTreeExtensionPropertyGroup,
]

if bpy.app.version >= (4, 1):
    classes.extend(
        [
            file_handler.VRM_FH_vrm_import,
            file_handler.VRM_FH_vrma_import,
        ]
    )


def register() -> None:
    name = ".".join(__name__.split(".")[:-1])
    logger.debug("Registering: %s", name)

    bpy.app.translations.register(
        preferences.addon_package_name,
        translation_dictionary,
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    NodeTree.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonNodeTreeExtensionPropertyGroup
    )

    Material.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonMaterialExtensionPropertyGroup
    )

    Scene.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonSceneExtensionPropertyGroup
    )

    Bone.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonBoneExtensionPropertyGroup
    )

    Armature.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonArmatureExtensionPropertyGroup
    )

    Object.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonObjectExtensionPropertyGroup
    )

    TOPBAR_MT_file_import.append(import_scene.menu_import)
    TOPBAR_MT_file_export.append(export_scene.menu_export)
    VIEW3D_MT_armature_add.append(panel.add_armature)
    # VIEW3D_MT_mesh_add.append(panel.make_mesh)

    bpy.app.handlers.load_post.append(handler.load_post)
    bpy.app.handlers.load_post.append(mtoon1_handler.load_post)
    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.depsgraph_update_pre.append(
        depsgraph_update_pre_once_if_load_post_is_unavailable
    )
    bpy.app.handlers.depsgraph_update_pre.append(depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.append(vrm1_handler.depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.append(mtoon1_handler.depsgraph_update_pre)
    bpy.app.handlers.save_pre.append(save_pre)
    bpy.app.handlers.save_pre.append(vrm1_handler.save_pre)
    bpy.app.handlers.save_pre.append(mtoon1_handler.save_pre)
    bpy.app.handlers.frame_change_pre.append(spring_bone1_handler.frame_change_pre)
    bpy.app.handlers.frame_change_pre.append(vrm0_handler.frame_change_pre)
    bpy.app.handlers.frame_change_post.append(vrm0_handler.frame_change_post)
    bpy.app.handlers.frame_change_pre.append(vrm1_handler.frame_change_pre)
    bpy.app.handlers.frame_change_post.append(vrm1_handler.frame_change_post)
    bpy.app.handlers.depsgraph_update_pre.append(
        spring_bone1_handler.depsgraph_update_pre
    )

    io_scene_gltf2_support.init_extras_export()

    # --- Begin SpringBone Modal Operator Registration Code ---
    # Import the modal operator from spring_bone1_handler
    from .editor.spring_bone1 import handler as spring_bone1_handler_modal

    classes_modal = [
        spring_bone1_handler_modal.SPRINGBONE_OT_viewport_modal_update,
    ]

    def register_modal() -> None:
        bpy.app.handlers.depsgraph_update_pre.append(
            spring_bone1_handler_modal.depsgraph_update_pre
        )
        bpy.app.handlers.frame_change_pre.append(
            spring_bone1_handler_modal.frame_change_pre
        )
        bpy.app.handlers.load_post.append(
            spring_bone1_handler_modal.springbone_delayed_start
        )
        for cls in classes_modal:
            bpy.utils.register_class(cls)

    register_modal()
    # --- End SpringBone Modal Operator Registration Code ---

    # --- Begin VRM0 Secondary Animation Modal Operator Registration Code ---
    from .editor.vrm0 import handler as vrm0_handler_modal

    classes_modal_vrm0 = [
        vrm0_handler_modal.VRM0OTSecondaryAnimationViewportModalUpdate,
    ]

    def register_modal_vrm0() -> None:
        bpy.app.handlers.depsgraph_update_pre.append(
            vrm0_handler_modal.secondary_animation_frame_change_pre
        )
        bpy.app.handlers.frame_change_pre.append(
            vrm0_handler_modal.secondary_animation_frame_change_pre
        )
        bpy.app.handlers.load_post.append(
            vrm0_handler_modal.vrm0_secondary_animation_delayed_start
        )
        for cls in classes_modal_vrm0:
            bpy.utils.register_class(cls)

    register_modal_vrm0()
    # --- End VRM0 Secondary Animation Modal Operator Registration Code ---

    logger.debug("Registered: %s", name)


def unregister() -> None:
    subscription.teardown_subscription()

    bpy.app.handlers.depsgraph_update_pre.remove(
        spring_bone1_handler.depsgraph_update_pre
    )
    bpy.app.handlers.frame_change_post.remove(vrm1_handler.frame_change_post)
    bpy.app.handlers.frame_change_pre.remove(vrm1_handler.frame_change_pre)
    bpy.app.handlers.frame_change_post.remove(vrm0_handler.frame_change_post)
    bpy.app.handlers.frame_change_pre.remove(vrm0_handler.frame_change_pre)
    bpy.app.handlers.frame_change_pre.remove(spring_bone1_handler.frame_change_pre)
    bpy.app.handlers.save_pre.remove(mtoon1_handler.save_pre)
    bpy.app.handlers.save_pre.remove(vrm1_handler.save_pre)
    bpy.app.handlers.save_pre.remove(save_pre)
    bpy.app.handlers.depsgraph_update_pre.remove(mtoon1_handler.depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.remove(vrm1_handler.depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_update_pre)
    if (
        depsgraph_update_pre_once_if_load_post_is_unavailable
        in bpy.app.handlers.depsgraph_update_pre
    ):
        bpy.app.handlers.depsgraph_update_pre.remove(
            depsgraph_update_pre_once_if_load_post_is_unavailable
        )
    bpy.app.handlers.load_post.remove(load_post)
    bpy.app.handlers.load_post.remove(mtoon1_handler.load_post)
    bpy.app.handlers.load_post.remove(handler.load_post)

    # VIEW3D_MT_mesh_add.remove(panel.make_mesh)
    VIEW3D_MT_armature_add.remove(panel.add_armature)
    TOPBAR_MT_file_export.remove(export_scene.menu_export)
    TOPBAR_MT_file_import.remove(import_scene.menu_import)

    if hasattr(Object, "vrm_addon_extension"):
        del Object.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    if hasattr(Armature, "vrm_addon_extension"):
        del Armature.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    if hasattr(Bone, "vrm_addon_extension"):
        del Bone.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    if hasattr(Scene, "vrm_addon_extension"):
        del Scene.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    if hasattr(Material, "vrm_addon_extension"):
        del Material.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    if hasattr(NodeTree, "vrm_addon_extension"):
        del NodeTree.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            logger.exception("Failed to Unregister %s", cls)

    # --- Begin SpringBone Modal Operator Unregistration Code ---
    def unregister_modal() -> None:
        try:  # noqa: SIM105
            bpy.app.handlers.load_post.remove(
                spring_bone1_handler_modal.springbone_delayed_start  # type: ignore[valid-type]  # noqa: F821
            )
        except ValueError:
            pass
        bpy.app.handlers.depsgraph_update_pre.remove(
            spring_bone1_handler_modal.depsgraph_update_pre  # type: ignore[valid-type]  # noqa: F821
        )
        bpy.app.handlers.frame_change_pre.remove(
            spring_bone1_handler_modal.frame_change_pre  # type: ignore[valid-type]  # noqa: F821
        )
        for cls in classes_modal:  # type: ignore[valid-type]  # noqa: F821
            bpy.utils.unregister_class(cls)  # type: ignore[valid-type]

    unregister_modal()
    # --- End SpringBone Modal Operator Unregistration Code ---

    # --- Begin VRM0 Secondary Animation Modal Operator Unregistration Code ---
    def unregister_modal_vrm0() -> None:
        try:  # noqa: SIM105
            bpy.app.handlers.load_post.remove(
                vrm0_handler_modal.vrm0_secondary_animation_delayed_start  # type: ignore[valid-type]  # noqa: F821
            )
        except ValueError:
            pass
        bpy.app.handlers.depsgraph_update_pre.remove(
            vrm0_handler_modal.secondary_animation_frame_change_pre  # type: ignore[valid-type]  # noqa: F821
        )
        bpy.app.handlers.frame_change_pre.remove(
            vrm0_handler_modal.secondary_animation_frame_change_pre  # type: ignore[valid-type]  # noqa: F821
        )
        for cls in classes_modal_vrm0:  # type: ignore[valid-type]  # noqa: F821
            bpy.utils.unregister_class(cls)  # type: ignore[valid-type]

    unregister_modal_vrm0()
    # --- End VRM0 Secondary Animation Modal Operator Unregistration Code ---

    bpy.app.translations.unregister(preferences.addon_package_name)
