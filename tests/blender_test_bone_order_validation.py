import bpy


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]
    humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    spine_bone = [b for b in humanoid.human_bones if b.bone == "spine"][0]
    chest_bone = [b for b in humanoid.human_bones if b.bone == "chest"][0]
    spine_bone.node.value = "chest"
    chest_bone.node.value = "spine"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    spine_bone.node.value = "spine"
    chest_bone.node.value = "chest"
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    right_little_distal_bone = [
        b for b in humanoid.human_bones if b.bone == "rightLittleDistal"
    ][0]
    right_little_distal_bone.node.value = "spine"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.value = "hips"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.value = "little.distal.L"
    assert bpy.ops.vrm.model_validate() == {"CANCELLED"}
    right_little_distal_bone.node.value = ""
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}
    right_little_distal_bone.node.value = "little.distal.R"
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}


if __name__ == "__main__":
    test()
