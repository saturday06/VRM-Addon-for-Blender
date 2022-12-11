import os
import pathlib
import platform
import shutil
import sys
from typing import List

import bpy

from io_scene_vrm.common.logging import get_logger
from io_scene_vrm.importer.vrm_diff import vrm_diff

logger = get_logger(__name__)

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
vrm_dir = os.path.join(
    os.environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        os.path.join(repository_root_dir, "tests", "resources"),
    ),
    "vrm",
)


def get_test_command_args() -> List[List[str]]:
    command_args: List[List[str]] = []
    for (vrm, extract_textures) in [
        (v, e)
        for e in ["false", "true"]
        for v in sorted(os.listdir(os.path.join(vrm_dir, "in")))
        if v.endswith(".vrm")
    ]:
        command_args.append([vrm, extract_textures])
    return command_args


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_failed_vrm = os.environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"

    vrm, extract_textures_str = sys.argv[sys.argv.index("--") + 1 :]
    in_path = os.path.join(vrm_dir, "in", vrm)

    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    out_vrm_dir = os.path.join(vrm_dir, major_minor, "out")
    temp_vrm_dir = os.path.join(vrm_dir, major_minor, "temp")
    os.makedirs(temp_vrm_dir, exist_ok=True)
    extract_textures = extract_textures_str == "true"

    if not os.path.exists(os.path.join(out_vrm_dir, vrm)):
        update_failed_vrm = True

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.import_scene.vrm(
        filepath=in_path,
        extract_textures_into_folder=extract_textures,
        make_new_texture_folder=extract_textures,
    )

    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    actual_path = os.path.join(temp_vrm_dir, os.path.basename(in_path))
    if os.path.exists(actual_path):
        os.remove(actual_path)

    bpy.ops.export_scene.vrm(filepath=actual_path)
    actual_bytes = pathlib.Path(actual_path).read_bytes()

    system = platform.system()
    if system in ["Darwin", "Linux"]:
        float_tolerance = 0.00055
    else:
        float_tolerance = 0.00030

    expected_path = os.path.join(out_vrm_dir, vrm)
    if not os.path.exists(expected_path):
        shutil.copy(actual_path, expected_path)

    diffs = vrm_diff(
        actual_bytes,
        pathlib.Path(expected_path).read_bytes(),
        float_tolerance,
    )
    if not diffs:
        return

    if update_failed_vrm:
        shutil.copy(actual_path, expected_path)

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
