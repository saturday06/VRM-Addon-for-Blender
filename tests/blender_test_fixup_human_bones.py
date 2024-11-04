# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from bpy.types import Armature, Context

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm0.human_bone import HumanBoneName
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.vrm0.property_group import Vrm0HumanoidPropertyGroup


def test(context: Context) -> None:
    ops.icyp.make_basic_armature()
    armatures = [obj for obj in context.blend_data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]
    if not isinstance(armature.data, Armature):
        raise TypeError

    human_bones = get_armature_extension(armature.data).vrm0.humanoid.human_bones

    original = [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

    human_bone1 = human_bones.add()
    human_bone1.bone = "NoHumanBone"
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

    human_bone2 = human_bones.add()
    human_bone2.bone = HumanBoneName.CHEST.value
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

    human_bones.add()
    human_bones.add()
    human_bones.add()
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert original == [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

    chest_bone = next(b for b in human_bones if b.bone == HumanBoneName.CHEST.value)
    spine_bone = next(b for b in human_bones if b.bone == HumanBoneName.SPINE.value)
    chest_bone.node.bone_name = HumanBoneName.SPINE.value
    assert spine_bone.node.bone_name == HumanBoneName.SPINE.value
    assert chest_bone.node.bone_name == HumanBoneName.SPINE.value
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    assert spine_bone.node.bone_name == HumanBoneName.SPINE.value
    assert not chest_bone.node.bone_name
    chest_bone.node.bone_name = HumanBoneName.CHEST.value
    assert original == [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

    hips_index = next(
        i for i, b in enumerate(human_bones) if b.bone == HumanBoneName.HIPS.value
    )
    human_bones.remove(hips_index)
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    hips_bone = next(b for b in human_bones if b.bone == HumanBoneName.HIPS.value)
    assert not hips_bone.node.bone_name
    hips_bone.node.bone_name = "hips"
    assert set(original) == {(str(b.node.bone_name), str(b.bone)) for b in human_bones}


if __name__ == "__main__":
    test(bpy.context)
