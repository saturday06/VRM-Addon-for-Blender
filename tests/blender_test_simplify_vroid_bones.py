import bpy


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    print(str(armatures))
    assert len(armatures) == 1
    armature = armatures[0]

    head = armature.data.bones["head"]
    head.name = "J_Bip_C_Head"
    eye_l = armature.data.bones["eye.L"]
    eye_l.name = "J_Adj_L_FaceEye"
    upper_arm_r = armature.data.bones["upper_arm.R"]
    upper_arm_r.name = "J_Sec_R_UpperArm"

    bpy.ops.vrm.bones_rename(armature_name=armature.name)

    assert head == armature.data.bones["Head"]
    assert eye_l == armature.data.bones["FaceEye_L"]
    assert upper_arm_r == armature.data.bones["UpperArm_R"]


if __name__ == "__main__":
    test()
