import os
import pathlib
import platform
import shutil
import sys
from typing import List

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.vrm_diff import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
resources_dir = os.environ.get(
    "BLENDER_VRM_TEST_RESOURCES_PATH",
    os.path.join(repository_root_dir, "tests", "resources"),
)
vrm_dir = os.path.join(resources_dir, "vrm")
blend_dir = os.path.join(resources_dir, "blend")


def get_test_command_args() -> List[List[str]]:
    names = [
        blend_path.name for blend_path in pathlib.Path(blend_dir).glob("**/*.blend")
    ]
    command_args: List[List[str]] = [
        [name] for name in sorted(list(dict.fromkeys(names)))
    ]
    return command_args


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_failed_vrm = os.environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"
    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"

    blend = sys.argv[sys.argv.index("--") + 1]
    in_path = os.path.join(blend_dir, blend)
    if not os.path.exists(in_path):
        in_path = os.path.join(blend_dir, major_minor, blend)

    vrm = os.path.splitext(blend)[0] + ".vrm"
    blend_vrm_path = os.path.join(vrm_dir, major_minor, "out", blend + ".vrm")
    expected_path = blend_vrm_path
    if not os.path.exists(expected_path):
        expected_path = os.path.join(vrm_dir, major_minor, "out", vrm)
        if not os.path.exists(expected_path):
            expected_path = os.path.join(vrm_dir, "in", vrm)
    temp_vrm_dir = os.path.join(vrm_dir, major_minor, "temp")
    os.makedirs(temp_vrm_dir, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=in_path)

    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_vrm_dir, vrm)
    if os.path.exists(actual_path):
        os.remove(actual_path)
    bpy.ops.export_scene.vrm(filepath=actual_path)

    system = platform.system()
    if system in ["Darwin", "Linux"]:
        float_tolerance = 0.00003
    else:
        float_tolerance = 0.00001

    diffs = vrm_diff(
        pathlib.Path(actual_path).read_bytes(),
        pathlib.Path(expected_path).read_bytes(),
        float_tolerance,
    )
    if not diffs:
        return

    if update_failed_vrm:
        shutil.copy(actual_path, blend_vrm_path)

    diffs_str = "\n".join(diffs)
    message = (
        f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
        + f"input={in_path}\n"
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
