import os
import pathlib
import shutil
import sys
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

    repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    vrm_dir = os.environ.get(
        "BLENDER_VRM_TEST_VRM_DIR",
        os.path.join(repository_root_dir, "tests", "vrm"),
    )
    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = "basic_armature.vrm"
    expected_path = os.path.join(vrm_dir, major_minor, "out", vrm)
    temp_dir_path = os.path.join(vrm_dir, major_minor, "temp")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.icyp.make_basic_armature()
    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_dir_path, "basic_armature.vrm")
    bpy.ops.export_scene.vrm(filepath=actual_path)
    if not os.path.exists(expected_path):
        shutil.copy(actual_path, expected_path)

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


if __name__ == "__main__":
    test()
