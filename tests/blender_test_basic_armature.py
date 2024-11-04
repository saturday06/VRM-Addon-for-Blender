# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import shutil
import sys
from os import environ, getenv
from pathlib import Path

import bpy
from bpy.types import Context

from io_scene_vrm.common import ops
from io_scene_vrm.importer.vrm_diff import vrm_diff


def test(context: Context) -> None:
    environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

    repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
    vrm_dir = Path(
        environ.get(
            "BLENDER_VRM_TEST_RESOURCES_PATH",
            str(repository_root_dir / "tests" / "resources"),
        ),
        "vrm",
    )
    major_minor = getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = Path("basic_armature.vrm")
    expected_path = vrm_dir / "in" / vrm
    temp_dir_path = vrm_dir / major_minor / "temp"
    temp_dir_path.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])

    ops.icyp.make_basic_armature()
    assert ops.vrm.model_validate() == {"FINISHED"}

    actual_path = temp_dir_path / ("test_basic_armature." + vrm.name)
    if actual_path.exists():
        actual_path.unlink()
    ops.export_scene.vrm(filepath=str(actual_path))
    if not expected_path.exists():
        shutil.copy(actual_path, expected_path)

    float_tolerance = 0.000001
    diffs = vrm_diff(
        actual_path.read_bytes(),
        expected_path.read_bytes(),
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
    if sys.platform == "win32":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test(bpy.context)
