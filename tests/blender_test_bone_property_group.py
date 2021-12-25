import sys
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.editor.property_group import BonePropertyGroup  # noqa: E402

# pylint: enable=wrong-import-position;


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    print(str(armatures))
    assert len(armatures) == 1
    armature = armatures[0]

    for props in BonePropertyGroup.get_all_bone_property_groups(armature):
        assert isinstance(props, BonePropertyGroup)


if __name__ == "main":
    test()
