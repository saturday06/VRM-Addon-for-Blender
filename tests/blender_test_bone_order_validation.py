import bpy
from bpy.types import Armature


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]
    if not isinstance(armature.data, Armature):
        raise TypeError

    humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
    chest_bone = next(b for b in humanoid.human_bones if b.bone == "chest")
    spine_bone.node.bone_name = "chest"
    chest_bone.node.bone_name = "spine"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    spine_bone.node.bone_name = "spine"
    chest_bone.node.bone_name = "chest"
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    right_little_distal_bone = next(
        b for b in humanoid.human_bones if b.bone == "rightLittleDistal"
    )
    right_little_distal_bone.node.bone_name = "spine"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.bone_name = "hips"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.bone_name = "little_distal.L"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.bone_name = ""
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}
    right_little_distal_bone.node.bone_name = "little_distal.R"
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}


if __name__ == "__main__":
    test()
