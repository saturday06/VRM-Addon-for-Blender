import functools
from typing import Dict

import bpy

from ...common.human_bone import HumanBone, HumanBoneName
from ..property_group import BonePropertyGroup, MeshPropertyGroup, StringPropertyGroup


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.humanBones.humanBone.schema.json
class Vrm1HumanBonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=BonePropertyGroup  # noqa: F722
    )

    # for UI
    node_candidates: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    def update_node_candidates(
        self,
        armature_data: bpy.types.Armature,
        target: HumanBone,
        blender_bone_name_to_human_bone_dict: Dict[str, HumanBone],
    ) -> None:
        new_candidates = BonePropertyGroup.find_bone_candidates(
            armature_data,
            target,
            blender_bone_name_to_human_bone_dict,
        )
        if set(map(lambda n: n.value, self.node_candidates)) == new_candidates:
            return

        self.node_candidates.clear()
        # Preserving list order
        for bone_name in armature_data.bones.keys():
            if bone_name not in new_candidates:
                continue
            candidate = self.node_candidates.add()
            candidate.value = bone_name  # for logic
            candidate.name = bone_name  # for view


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.humanBones.schema.json
class Vrm1HumanBonesPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    hips: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    spine: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    chest: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    upper_chest: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    neck: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    head: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_eye: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_eye: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    jaw: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_upper_leg: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_lower_leg: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_foot: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_toes: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_upper_leg: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_lower_leg: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_foot: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_toes: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_shoulder: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_upper_arm: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_lower_arm: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_hand: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_shoulder: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_upper_arm: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_lower_arm: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_hand: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_thumb_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_thumb_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_thumb_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_index_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_index_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_index_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_middle_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_middle_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_middle_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_ring_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_ring_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_ring_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_little_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_little_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    left_little_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_thumb_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_thumb_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_thumb_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_index_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_index_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_index_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_middle_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_middle_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_middle_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_ring_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_ring_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_ring_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_little_proximal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_little_intermediate: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )
    right_little_distal: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup  # noqa: F722
    )

    # for UI
    last_bone_names: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    def human_bone_to_human_bone_props(
        self,
    ) -> Dict[HumanBoneName, Vrm1HumanBonePropertyGroup]:
        return {
            HumanBoneName.HIPS: self.hips,
            HumanBoneName.SPINE: self.spine,
            HumanBoneName.CHEST: self.chest,
            HumanBoneName.UPPER_CHEST: self.upper_chest,
            HumanBoneName.NECK: self.neck,
            HumanBoneName.HEAD: self.head,
            HumanBoneName.LEFT_EYE: self.left_eye,
            HumanBoneName.RIGHT_EYE: self.right_eye,
            HumanBoneName.JAW: self.jaw,
            HumanBoneName.LEFT_UPPER_LEG: self.left_upper_leg,
            HumanBoneName.LEFT_LOWER_LEG: self.left_lower_leg,
            HumanBoneName.LEFT_FOOT: self.left_foot,
            HumanBoneName.LEFT_TOES: self.left_toes,
            HumanBoneName.RIGHT_UPPER_LEG: self.right_upper_leg,
            HumanBoneName.RIGHT_LOWER_LEG: self.right_lower_leg,
            HumanBoneName.RIGHT_FOOT: self.right_foot,
            HumanBoneName.RIGHT_TOES: self.right_toes,
            HumanBoneName.LEFT_SHOULDER: self.left_shoulder,
            HumanBoneName.LEFT_UPPER_ARM: self.left_upper_arm,
            HumanBoneName.LEFT_LOWER_ARM: self.left_lower_arm,
            HumanBoneName.LEFT_HAND: self.left_hand,
            HumanBoneName.RIGHT_SHOULDER: self.right_shoulder,
            HumanBoneName.RIGHT_UPPER_ARM: self.right_upper_arm,
            HumanBoneName.RIGHT_LOWER_ARM: self.right_lower_arm,
            HumanBoneName.RIGHT_HAND: self.right_hand,
            HumanBoneName.LEFT_THUMB_PROXIMAL: self.left_thumb_proximal,
            HumanBoneName.LEFT_THUMB_INTERMEDIATE: self.left_thumb_intermediate,
            HumanBoneName.LEFT_THUMB_DISTAL: self.left_thumb_distal,
            HumanBoneName.LEFT_INDEX_PROXIMAL: self.left_index_proximal,
            HumanBoneName.LEFT_INDEX_INTERMEDIATE: self.left_index_intermediate,
            HumanBoneName.LEFT_INDEX_DISTAL: self.left_index_distal,
            HumanBoneName.LEFT_MIDDLE_PROXIMAL: self.left_middle_proximal,
            HumanBoneName.LEFT_MIDDLE_INTERMEDIATE: self.left_middle_intermediate,
            HumanBoneName.LEFT_MIDDLE_DISTAL: self.left_middle_distal,
            HumanBoneName.LEFT_RING_PROXIMAL: self.left_ring_proximal,
            HumanBoneName.LEFT_RING_INTERMEDIATE: self.left_ring_intermediate,
            HumanBoneName.LEFT_RING_DISTAL: self.left_ring_distal,
            HumanBoneName.LEFT_LITTLE_PROXIMAL: self.left_little_proximal,
            HumanBoneName.LEFT_LITTLE_INTERMEDIATE: self.left_little_intermediate,
            HumanBoneName.LEFT_LITTLE_DISTAL: self.left_little_distal,
            HumanBoneName.RIGHT_THUMB_PROXIMAL: self.right_thumb_proximal,
            HumanBoneName.RIGHT_THUMB_INTERMEDIATE: self.right_thumb_intermediate,
            HumanBoneName.RIGHT_THUMB_DISTAL: self.right_thumb_distal,
            HumanBoneName.RIGHT_INDEX_PROXIMAL: self.right_index_proximal,
            HumanBoneName.RIGHT_INDEX_INTERMEDIATE: self.right_index_intermediate,
            HumanBoneName.RIGHT_INDEX_DISTAL: self.right_index_distal,
            HumanBoneName.RIGHT_MIDDLE_PROXIMAL: self.right_middle_proximal,
            HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE: self.right_middle_intermediate,
            HumanBoneName.RIGHT_MIDDLE_DISTAL: self.right_middle_distal,
            HumanBoneName.RIGHT_RING_PROXIMAL: self.right_ring_proximal,
            HumanBoneName.RIGHT_RING_INTERMEDIATE: self.right_ring_intermediate,
            HumanBoneName.RIGHT_RING_DISTAL: self.right_ring_distal,
            HumanBoneName.RIGHT_LITTLE_PROXIMAL: self.right_little_proximal,
            HumanBoneName.RIGHT_LITTLE_INTERMEDIATE: self.right_little_intermediate,
            HumanBoneName.RIGHT_LITTLE_DISTAL: self.right_little_distal,
        }

    @staticmethod
    def check_last_bone_names_and_update(
        armature_data_name: str,
        defer: bool = True,
    ) -> None:
        armature_data = bpy.data.armatures.get(armature_data_name)
        if not armature_data:
            return
        human_bones_props = (
            armature_data.vrm_addon_extension.vrm1.vrm.humanoid.human_bones
        )
        bone_names = sorted(armature_data.bones.keys())
        up_to_date = bone_names == list(
            map(lambda n: str(n.value), human_bones_props.last_bone_names)
        )

        if up_to_date:
            return

        if defer:
            bpy.app.timers.register(
                functools.partial(
                    Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update,
                    armature_data_name,
                    False,
                )
            )
            return

        human_bones_props.last_bone_names.clear()
        for bone_name in bone_names:
            bone_name_props = human_bones_props.last_bone_names.add()
            bone_name_props.value = bone_name
        blender_bone_name_to_human_bone_dict: Dict[str, HumanBone] = {
            human_bone_props.node.value: human_bone
            for human_bone, human_bone_props in human_bones_props.human_bone_to_human_bone_props()
            if human_bone_props.node.value
        }

        for human_bone in human_bones_props.human_bone_to_human_bone_props().values():
            human_bone.update_node_candidates(
                armature_data,
                blender_bone_name_to_human_bone_dict,
            )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.schema.json
class Vrm1HumanoidPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    human_bones: bpy.props.PointerProperty(type=Vrm1HumanBonesPropertyGroup)  # type: ignore[valid-type]

    # for T-Pose
    pose_library: bpy.props.PointerProperty(type=bpy.types.Action)  # type: ignore[valid-type]
    pose_marker_name: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.lookAt.rangeMap.schema.json
class Vrm1LookAtRangeMapPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    input_max_value: bpy.props.FloatProperty()  # type: ignore[valid-type]
    output_scale: bpy.props.FloatProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.lookAt.schema.json
class Vrm1LookAtPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    offset_from_head_bone: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    type_items = [
        ("Bone", "Bone", "Bone", "BONE_DATA", 0),
        ("Expression", "Expression", "Expression", "SHAPEKEY_DATA", 1),
    ]
    type: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=type_items,  # noqa: F722
    )
    range_map_horizontal_inner: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,  # noqa: F722
    )
    range_map_horizontal_outer: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,  # noqa: F722
    )
    range_map_vertical_down: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup  # noqa: F722
    )
    range_map_vertical_up: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.firstPerson.meshAnnotation.schema.json
class Vrm1MeshAnnotationPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=MeshPropertyGroup  # noqa: F821
    )
    first_person_flag_items = [
        ("Auto", "Auto", "", 0),
        ("Both", "Both", "", 1),
        ("ThirdPersonOnly", "Third-Person Only", "", 2),
        ("FirstPersonOnly", "First-Person Only", "", 3),
    ]
    first_person_flag: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_items, name="First Person Flag"  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.firstPerson.schema.json
class Vrm1FirstPersonPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    mesh_annotations: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations", type=Vrm1MeshAnnotationPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.morphTargetBind.schema.json
class Vrm1MorphTargetBindPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=MeshPropertyGroup  # noqa: F821
    )
    index: bpy.props.StringProperty(  # type: ignore[valid-type]
        # noqa: F821
    )
    weight: bpy.props.FloatProperty(  # type: ignore[valid-type]
        min=0, max=1  # noqa: F821
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.materialColorBind.schema.json
class Vrm1MaterialColorBindPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    material: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Material  # noqa: F821
    )

    type_items = [
        ("color", "Color", "", 0),
        ("emissionColor", "Emission Color", "", 1),
        ("shadeColor", "Shade Color", "", 2),
        ("rimColor", "Rim Color", "", 3),
        ("outlineColor", "Outline Color", "", 4),
    ]
    type: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=type_items  # noqa: F722
    )
    target_value: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=4  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.textureTransformBind.schema.json
class Vrm1TextureTransformBindPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    material: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Material  # noqa: F821
    )
    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=2, default=(0, 0)  # noqa: F722
    )
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=2, default=(0, 0)  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.schema.json
class Vrm1ExpressionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    morph_target_binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1MorphTargetBindPropertyGroup  # noqa: F821
    )
    material_color_binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1MaterialColorBindPropertyGroup  # noqa: F722
    )
    texture_transform_binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1TextureTransformBindPropertyGroup  # noqa: F722
    )
    is_binary: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Is Binary"  # noqa: F722
    )

    expression_override_type_items = [
        ("none", "None", "", 0),
        ("block", "Block", "", 1),
        ("blend", "Blend", "", 2),
    ]

    override_blink: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Override Blink", items=expression_override_type_items  # noqa: F722
    )
    override_look_at: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Override Look At", items=expression_override_type_items  # noqa: F722
    )
    override_mouth: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Override Mouth", items=expression_override_type_items  # noqa: F722
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
    show_expanded_morph_target_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Morph Target Binds"  # noqa: F722
    )
    show_expanded_material_color_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Material Color Binds"  # noqa: F722
    )
    show_expanded_texture_transform_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Texture Transform Binds"  # noqa: F722
    )


class Vrm1CustomExpressionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    custom_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    expression: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.schema.json
class Vrm1ExpressionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    happy: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    angry: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    sad: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    relaxed: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    surprised: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    neutral: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    aa: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ih: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ou: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ee: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    oh: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink_left: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink_right: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_up: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_down: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_left: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_right: bpy.props.PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]

    custom: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1CustomExpressionPropertyGroup  # noqa: F722
    )

    def preset_name_to_expression_dict(self) -> Dict[str, Vrm1ExpressionPropertyGroup]:
        return {
            "happy": self.happy,
            "angry": self.angry,
            "sad": self.sad,
            "relaxed": self.relaxed,
            "surprised": self.surprised,
            "neutral": self.neutral,
            "aa": self.aa,
            "ih": self.ih,
            "ou": self.ou,
            "ee": self.ee,
            "oh": self.oh,
            "blink": self.blink,
            "blinkLeft": self.blink_left,
            "blinkRight": self.blink_right,
            "lookUp": self.look_up,
            "lookDown": self.look_down,
            "lookLeft": self.look_left,
            "lookRight": self.look_right,
        }

    def all_name_to_expression_dict(self) -> Dict[str, Vrm1ExpressionPropertyGroup]:
        result = self.preset_name_to_expression_dict()
        for custom_props in self.custom:
            result[custom_props.custom_name] = custom_props.expression
        return result


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L7-L27
class Vrm1ColliderShapeSpherePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    radius: bpy.props.FloatProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L28-L58
class Vrm1ColliderShapeCapsulePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    radius: bpy.props.FloatProperty()  # type: ignore[valid-type]
    tail: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json
class Vrm1ColliderShapePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    sphere: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ColliderShapeSpherePropertyGroup  # noqa: F722
    )
    capsule: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ColliderShapeCapsulePropertyGroup  # noqa: F722
    )

    # for UI
    SHAPE_SPHERE = "Sphere"
    SHAPE_CAPSULE = "Capsule"
    shape_items = [
        (SHAPE_SPHERE, "Sphere", "", 0),
        (SHAPE_CAPSULE, "Capsule", "", 1),
    ]
    shape: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=shape_items,  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.collider.schema.json
class Vrm1ColliderPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    shape: bpy.props.PointerProperty(type=Vrm1ColliderShapePropertyGroup)  # type: ignore[valid-type]

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for View3D
    blender_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

    def refresh(self, armature: bpy.types.Object, bone_name: str) -> None:
        if not self.node or not self.node.name:
            return

        self.node.name = self.node.name
        self.node.parent = armature
        self.node.empty_display_type = "SPHERE"
        if bone_name:
            self.node.parent_type = "BONE"
            self.node.parent_bone = bone_name
        else:
            self.node.parent_type = "OBJECT"


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
class Vrm1ColliderGroupPropertyGroup(
    bpy.types.PropertyGroup, bpy.types.ID  # type: ignore[misc]
):
    name: bpy.props.StringProperty()  # type: ignore[valid-type]
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=Vrm1ColliderPropertyGroup  # noqa: F821
    )

    def refresh(self, armature: bpy.types.Object) -> None:
        self.name = (
            str(self.node.value) if self.node and self.node.value else ""
        ) + f"#{self.uuid}"
        for index, collider in reversed(list(enumerate(list(self.colliders)))):
            if not collider.blender_object or not collider.blender_object.name:
                self.colliders.remove(index)
            else:
                collider.refresh(armature, self.node.value)
        for (
            bone_group
        ) in armature.data.vrm_addon_extension.vrm1.secondary_animation.bone_groups:
            bone_group.refresh(armature)

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for reference
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.joint.schema.json
class Vrm1JointPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    hit_radius: bpy.props.FloatProperty()  # type: ignore[valid-type]
    stiffness: bpy.props.FloatProperty()  # type: ignore[valid-type]
    gravity_power: bpy.props.FloatProperty()  # type: ignore[valid-type]
    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, default=(0, -1, 0)  # noqa: F722
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0, max=1.0
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.spring.schema.json
class Vrm1SpringPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    name: bpy.props.StringProperty()  # type: ignore[valid-type]
    joints: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1JointPropertyGroup
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
    show_expanded_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Bones"  # noqa: F821
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"  # noqa: F722
    )

    def refresh(self, armature: bpy.types.Object) -> None:
        collider_group_uuid_to_name = {
            collider_group.uuid: collider_group.name
            for collider_group in armature.data.vrm_addon_extension.vrm1.secondary_animation.collider_groups
        }
        for index, collider_group in reversed(list(enumerate(self.collider_groups))):
            uuid_str = collider_group.value.split("#")[-1:][0]
            name = collider_group_uuid_to_name.get(uuid_str)
            if name is None:
                self.collider_groups.remove(index)
            else:
                collider_group.value = name


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class Vrm1SpringBonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1ColliderPropertyGroup,
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1ColliderGroupPropertyGroup,
    )
    springs: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1SpringPropertyGroup,
    )

    # for UI
    show_expanded_colliders: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Colliders"  # noqa: F722
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Collider Groups"  # noqa: F722
    )
    show_expanded_springs: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Springs"  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.meta.schema.json
class Vrm1MetaPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    avatar_permission_items = [
        ("onlyAuthor", "Only Author", "", 0),
        ("onlySeparatelyLicensedPerson", "Only Separately Licensed Person", "", 1),
        ("everyone", "Everyone", "", 2),
    ]
    commercial_usage_items = [
        ("personalNonProfit", "Personal Non-Profit", "", 0),
        ("personalProfit", "Personal Profit", "", 1),
        ("corporation", "Corporation", "", 2),
    ]
    credit_notation_items = [
        ("required", "Required", "", 0),
        ("unnecessary", "Unnecessary", "", 1),
    ]
    modification_items = [
        ("prohibited", "Prohibited", "", 0),
        ("allowModification", "Allow Modification", "", 1),
        ("allowModificationRedistribution", "Allow Modification Redistribution", "", 2),
    ]
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )
    version: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Version"  # noqa: F821
    )
    authors: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup  # noqa: F821
    )
    copyright_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Copyright Information"  # noqa: F722
    )
    contact_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Contact Information"  # noqa: F722
    )
    references: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup  # noqa: F821
    )
    third_party_licenses: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Third Party Licenses"  # noqa: F722
    )
    thumbnail_image: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail Image", type=bpy.types.Image  # noqa: F722
    )
    license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="License URL"  # noqa: F722
    )
    avatar_permission: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Avatar Permission",  # noqa: F722
        items=avatar_permission_items,
    )
    allow_excessively_violent_usage: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Allow Excessively Violent Usage"  # noqa: F722
    )
    allow_excessively_sexual_usage: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Allow Excessively Sexual Usage"  # noqa: F722
    )
    commercial_usage: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Commercial Usage",  # noqa: F722
        items=commercial_usage_items,
    )
    allow_political_or_religious_usage: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Allow Political or Religious Usage"  # noqa: F722
    )
    allow_antisocial_or_hate_usage: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Allow Antisocial or Hate Usage"  # noqa: F722
    )
    credit_notation: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Credit Notation",  # noqa: F722
        items=credit_notation_items,
    )
    allow_redistribution: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Allow Redistribution"  # noqa: F722
    )
    modification: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Modification", items=modification_items  # noqa: F821
    )
    other_license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other License URL"  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.schema.json
class Vrm1VrmPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    meta: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1MetaPropertyGroup  # noqa: F722
    )
    humanoid: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanoidPropertyGroup  # noqa: F722
    )
    first_person: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1FirstPersonPropertyGroup  # noqa: F722
    )
    look_at: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtPropertyGroup  # noqa: F722
    )
    expressions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ExpressionsPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/
class Vrm1PropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    vrm: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1VrmPropertyGroup  # noqa: F722
    )
    spring_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1SpringBonePropertyGroup  # noqa: F722
    )
