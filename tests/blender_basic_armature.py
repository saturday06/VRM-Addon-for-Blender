import os
import pathlib
import sys
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import vrm_diff  # noqa: E402

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

float_tolerance = 0.000001
diffs = vrm_diff(
    pathlib.Path(actual_path).read_bytes(),
    pathlib.Path(expected_path).read_bytes(),
    float_tolerance,
)
diffs_str = "\n".join(diffs)

assert (
    len(diffs) == 0
), f"""Exceeded the VRM diff threshold::{float_tolerance:19.17f} for basic armature operator
left ={actual_path}
right={expected_path}
{diffs_str}"""
