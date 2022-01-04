import os
import pathlib
import platform
import shutil
import sys
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.vrm_diff import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

    repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    vrm_dir = os.path.join(
        os.environ.get(
            "BLENDER_VRM_TEST_RESOURCES_PATH",
            os.path.join(repository_root_dir, "tests", "resources"),
        ),
        "vrm",
    )
    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = "basic_armature.vrm"
    expected_path = os.path.join(vrm_dir, "in", vrm)
    temp_dir_path = os.path.join(vrm_dir, major_minor, "temp")
    os.makedirs(temp_dir_path, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.icyp.make_basic_armature()
    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_dir_path, "basic_armature.vrm")
    if os.path.exists(actual_path):
        os.remove(actual_path)
    bpy.ops.export_scene.vrm(filepath=actual_path)
    if not os.path.exists(expected_path):
        shutil.copy(actual_path, expected_path)

    float_tolerance = 0.000001
    diffs = vrm_diff(
        pathlib.Path(actual_path).read_bytes(),
        pathlib.Path(expected_path).read_bytes(),
        float_tolerance,
    )
    if not diffs:
        return

    diffs_str = "\n".join(diffs)
    message = (
        f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
        + f"left ={actual_path}\n"
        + f"right={expected_path}\n"
        + f"{diffs_str}\n"
    )
    if platform.system() == "Windows":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test()
