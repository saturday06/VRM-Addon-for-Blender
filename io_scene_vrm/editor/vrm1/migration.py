import bpy
from mathutils import Vector

from .property_group import Vrm1HumanBonesPropertyGroup, Vrm1PropertyGroup


def migrate(vrm1: Vrm1PropertyGroup, armature: bpy.types.Object) -> None:
    human_bones = vrm1.humanoid.human_bones
    human_bones.last_bone_names.clear()
    Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
    Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
        armature.data.name,
        defer=False,
    )

    if human_bones.initial_automatic_bone_assignment:
        human_bones.initial_automatic_bone_assignment = False
        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
        if all(not b.node.value for b in human_bone_name_to_human_bone.values()):
            bpy.ops.vrm.assign_vrm1_humanoid_human_bones_automatically(
                armature_name=armature.name
            )

    if tuple(armature.data.vrm_addon_extension.addon_version) <= (2, 14, 3):
        spring_bone1 = armature.data.vrm_addon_extension.spring_bone1
        for spring in spring_bone1.springs:
            for joint in spring.joints:
                joint.gravity_dir = [
                    joint.gravity_dir[0],
                    joint.gravity_dir[2],
                    joint.gravity_dir[1],
                ]

    if tuple(armature.data.vrm_addon_extension.addon_version) <= (2, 14, 10):
        head_bone_name = (
            armature.data.vrm_addon_extension.vrm1.humanoid.human_bones.head.node.value
        )
        head_bone = armature.data.bones.get(head_bone_name)
        if head_bone:
            look_at = armature.data.vrm_addon_extension.vrm1.look_at
            world_translation = (
                armature.matrix_world @ head_bone.matrix_local
            ).to_quaternion() @ Vector(look_at.offset_from_head_bone)
            look_at.offset_from_head_bone = list(world_translation)

        spring_bone1 = armature.data.vrm_addon_extension.spring_bone1
        for spring in spring_bone1.springs:
            for joint in spring.joints:
                joint.gravity_dir = [
                    joint.gravity_dir[0],
                    -joint.gravity_dir[1],
                    joint.gravity_dir[2],
                ]
