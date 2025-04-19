import cProfile
from pathlib import Path
from pstats import SortKey, Stats

import bpy
import requests
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)
from io_scene_vrm.editor.spring_bone1.handler import update_pose_bone_rotations

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def benchmark_spring_bone(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    clean_scene(context)

    url = "https://raw.githubusercontent.com/vrm-c/vrm-specification/c24d76d99a18738dd2c266be1c83f089064a7b5e/samples/VRM1_Constraint_Twist_Sample/vrm/VRM1_Constraint_Twist_Sample.vrm"
    path = Path(__file__).parent / "temp" / "VRM1_Constraint_Twist_Sample.vrm"
    if not path.exists():
        with requests.get(url, timeout=5 * 60) as response:
            assert response.ok
            path.write_bytes(response.content)

    assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}

    armature = context.object
    if (
        not armature
        or not (armature_data := armature.data)
        or not isinstance(armature_data, Armature)
    ):
        raise AssertionError

    get_armature_extension(armature_data).spring_bone1.enable_animation = True

    context.view_layer.update()
    update_pose_bone_rotations(context, delta_time=1.0 / 24.0)
    armature.location = Vector((1, 0, 0))
    context.view_layer.update()

    profiler = cProfile.Profile()
    with profiler:
        for _ in range(10):
            update_pose_bone_rotations(context, delta_time=1.0 / 24.0)

    Stats(profiler).sort_stats(SortKey.TIME).print_stats(50)


if __name__ == "__main__":
    benchmark_spring_bone(bpy.context)
