import sys

import bpy
from bpy.types import Armature, Context

from io_scene_vrm.importer.vrm0.vrm_importer import VrmImporter


def get_test_command_args() -> list[list[str]]:
    return [[key.__name__] for key in FUNCTIONS]


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def ignore_connected_head_child(
    context: Context,
) -> None:
    clean_scene(context)
    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError
    VrmImporter.setup_vrm0_humanoid_bones(context, armature)


def ignore_left_toe_child(
    context: Context,
) -> None:
    clean_scene(context)
    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError
    VrmImporter.setup_vrm0_humanoid_bones(context, armature)


FUNCTIONS = [
    ignore_connected_head_child,
    ignore_left_toe_child,
]


def test(context: Context, function_name: str) -> None:
    function = next((f for f in FUNCTIONS if f.__name__ == function_name), None)
    if function is None:
        message = f"No function name: {function_name}"
        raise AssertionError(message)
    function(context)


if __name__ == "__main__":
    context = bpy.context
    if "--" in sys.argv:
        test(context, *sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
    else:
        for arg in get_test_command_args():
            test(context, *arg)
