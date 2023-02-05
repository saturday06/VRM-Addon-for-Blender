import shutil
import sys
from os import environ, getenv
from pathlib import Path
from typing import List

import bpy

from io_scene_vrm.importer.vrm_diff import vrm_diff

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
resources_dir = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(repository_root_dir / "tests" / "resources"),
    )
)
vrm_dir = resources_dir / "vrm"
blend_dir = resources_dir / "blend"


def get_test_command_args() -> List[List[str]]:
    names = [blend_path.name for blend_path in blend_dir.glob("**/*.blend")]
    command_args: List[List[str]] = [
        [name] for name in sorted(list(dict.fromkeys(names)))
    ]
    return command_args


def test() -> None:
    environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"
    major_minor = getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"

    blend = Path(sys.argv[sys.argv.index("--") + 1])
    in_path = blend_dir / blend
    if not in_path.exists():
        in_path = blend_dir / major_minor / blend

    if blend.suffixes == [".merge", ".blend"]:
        blend = blend.with_suffix("").with_suffix(".blend")
    vrm = blend.with_suffix(".vrm")
    blend_vrm_path = vrm_dir / major_minor / "out" / blend.with_suffix(".blend.vrm")
    expected_path = blend_vrm_path
    if not expected_path.exists():
        expected_path = vrm_dir / major_minor / "out" / vrm
        if not expected_path.exists():
            expected_path = vrm_dir / "in" / vrm
    temp_vrm_dir = vrm_dir / major_minor / "temp"
    temp_vrm_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(in_path))

    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    actual_path = temp_vrm_dir / vrm
    if actual_path.exists():
        actual_path.unlink()
    bpy.ops.export_scene.vrm(filepath=str(actual_path))

    float_tolerance = 0.00015

    diffs = vrm_diff(
        actual_path.read_bytes(),
        expected_path.read_bytes(),
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
    if sys.platform == "win32":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test()
