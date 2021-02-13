import os
import pathlib
import sys
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.vrm_load import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;

os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

expected_path, temp_dir_path = sys.argv[sys.argv.index("--") + 1 :]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

bpy.ops.icyp.make_basic_armature()
bpy.ops.vrm.model_validate()

actual_path = os.path.join(temp_dir_path, "basic_armature.vrm")
bpy.ops.export_scene.vrm(filepath=actual_path)

diffs = vrm_diff(
    pathlib.Path(actual_path).read_bytes(),
    pathlib.Path(expected_path).read_bytes(),
    sys.float_info.epsilon,
)
diffs_str = "\n".join(diffs)

assert (
    len(diffs) == 0
), f"""Exceeded the VRM diff threshold for basic armature operator
left ={actual_path}
right={expected_path}
{diffs_str}"""
