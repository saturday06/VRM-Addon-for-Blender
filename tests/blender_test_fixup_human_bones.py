import bpy

from io_scene_vrm.common.vrm0.human_bone import HumanBoneName
from io_scene_vrm.editor.vrm0.property_group import Vrm0HumanoidPropertyGroup


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]

    human_bones = armature.data.vrm_addon_extension.vrm0.humanoid.human_bones

    original = list(map(lambda b: (str(b.node.value), str(b.bone)), human_bones))

    human_bone1 = human_bones.add()
    human_bone1.bone = "NoHumanBone"
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == list(
        map(lambda b: (str(b.node.value), str(b.bone)), human_bones)
    )

    human_bone2 = human_bones.add()
    human_bone2.bone = HumanBoneName.CHEST.value
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == list(
        map(lambda b: (str(b.node.value), str(b.bone)), human_bones)
    )

    human_bones.add()
    human_bones.add()
    human_bones.add()
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == list(
        map(lambda b: (str(b.node.value), str(b.bone)), human_bones)
    )

    chest_bone = list(
        filter(lambda b: b.bone == HumanBoneName.CHEST.value, human_bones)
    )[0]
    spine_bone = list(
        filter(lambda b: b.bone == HumanBoneName.SPINE.value, human_bones)
    )[0]
    chest_bone.node.value = HumanBoneName.SPINE.value
    assert spine_bone.node.value == HumanBoneName.SPINE.value
    assert chest_bone.node.value == HumanBoneName.SPINE.value
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert spine_bone.node.value == HumanBoneName.SPINE.value
    assert not chest_bone.node.value
    chest_bone.node.value = HumanBoneName.CHEST.value
    assert original == list(
        map(lambda b: (str(b.node.value), str(b.bone)), human_bones)
    )

    hips_index = next(
        i for i, b in enumerate(human_bones) if b.bone == HumanBoneName.HIPS.value
    )
    human_bones.remove(hips_index)
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    hips_bone = list(filter(lambda b: b.bone == HumanBoneName.HIPS.value, human_bones))[
        0
    ]
    assert not hips_bone.node.value
    hips_bone.node.value = "hips"
    assert set(original) == set(
        map(lambda b: (str(b.node.value), str(b.bone)), human_bones)
    )


if __name__ == "__main__":
    test()
