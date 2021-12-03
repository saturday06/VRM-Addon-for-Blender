import os
import pathlib
import platform
import shutil
import sys
from typing import List

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
vrm_dir = os.environ.get(
    "BLENDER_VRM_TEST_VRM_DIR", os.path.join(repository_root_dir, "tests", "vrm")
)
blend_dir = os.path.join(os.path.dirname(vrm_dir), "blend")


def get_test_command_args() -> List[List[str]]:
    command_args: List[List[str]] = []
    for blend in sorted(os.listdir(blend_dir)):
        if not blend.endswith(".blend"):
            continue
        command_args.append([blend])

    return command_args


def fix_stderr_encoding() -> None:
    if platform.system() == "Windows":
        sys.stderr.reconfigure(encoding="ansi")  # type: ignore


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "true"

    blend = sys.argv[sys.argv.index("--") + 1]
    in_path = os.path.join(blend_dir, blend)

    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = os.path.splitext(blend)[0] + ".vrm"
    expected_path = os.path.join(vrm_dir, major_minor, "out", vrm)
    temp_vrm_dir = os.path.join(vrm_dir, major_minor, "temp")

    bpy.ops.wm.open_mainfile(filepath=in_path)

    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_vrm_dir, vrm)
    bpy.ops.export_scene.vrm(filepath=actual_path)

    float_tolerance = 0.000001

    if not os.path.exists(expected_path):
        shutil.copy(actual_path, expected_path)

    diffs = vrm_diff(
        pathlib.Path(actual_path).read_bytes(),
        pathlib.Path(expected_path).read_bytes(),
        float_tolerance,
    )
    diffs_str = "\n".join(diffs)

    try:
        assert (
            len(diffs) == 0
        ), f"""Exceeded the VRM diff threshold::{float_tolerance:19.17f} for {in_path}
input={in_path}
left ={actual_path}
right={expected_path}
    {diffs_str}"""
    except AssertionError:
        if update_vrm_dir:
            shutil.copy(actual_path, expected_path)
        fix_stderr_encoding()
        raise


if __name__ == "__main__":
    test()
