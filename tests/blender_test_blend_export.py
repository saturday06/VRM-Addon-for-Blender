# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import shutil
import sys
from os import environ, getenv
from pathlib import Path

import bpy

from io_scene_vrm.common import ops
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


def get_test_command_args() -> list[list[str]]:
    names = [
        blend_path.name
        for blend_path in list(blend_dir.glob("*.blend"))
        + list(blend_dir.glob("*.*/*.blend"))
    ]
    command_args: list[list[str]] = [[name] for name in sorted(dict.fromkeys(names))]
    return command_args


def test(blend_path_str: str) -> None:
    environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"
    major_minor = getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    enable_second_export = not environ.get("BLENDER_VRM_TEST_RESOURCES_PATH")

    blend = Path(blend_path_str)
    in_path_default = blend_dir / blend
    in_path_versioned = blend_dir / major_minor / blend
    if in_path_default.exists():
        in_path = in_path_default
    elif in_path_versioned.exists():
        in_path = in_path_versioned
    else:
        message = f"No input file:\n{in_path_default}\n{in_path_versioned}\n"
        raise FileNotFoundError(message)

    if blend.name.endswith(".merge.blend"):
        blend = blend.with_suffix("").with_suffix(".blend")
    expected_path = vrm_dir / major_minor / "out" / "blend" / blend.with_suffix(".vrm")

    if Path(expected_path.with_suffix(expected_path.suffix + ".disabled")).exists():
        return

    temp_vrm_dir = vrm_dir / major_minor / "temp"
    temp_vrm_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(in_path))

    assert ops.vrm.model_validate() == {"FINISHED"}

    actual_path = temp_vrm_dir / ("test_blend_export." + expected_path.name)
    if actual_path.exists():
        actual_path.unlink()

    actual_second_path = temp_vrm_dir / ("test_blend_export.2nd." + expected_path.name)
    if actual_second_path.exists():
        actual_second_path.unlink()

    assert ops.export_scene.vrm(filepath=str(actual_path)) == {"FINISHED"}
    if enable_second_export:
        assert ops.export_scene.vrm(filepath=str(actual_second_path)) == {"FINISHED"}

    if not expected_path.exists():
        message = f"No expected result file: {expected_path}"
        raise FileNotFoundError(message)

    vrm_bin_diff(
        in_path,
        actual_path,
        expected_path,
        "Whether the export result is correct",
        update_failed_vrm=update_failed_vrm,
    )

    if enable_second_export:
        vrm_bin_diff(
            in_path,
            actual_path,
            actual_second_path,
            "The results of multiple exports are the same",
            update_failed_vrm=False,
        )


def vrm_bin_diff(
    in_path: Path,
    actual_path: Path,
    expected_path: Path,
    what: str,
    *,
    update_failed_vrm: bool,
) -> None:
    float_tolerance = 0.00015

    diffs = vrm_diff(
        actual_path.read_bytes(),
        expected_path.read_bytes(),
        float_tolerance,
    )
    if not diffs:
        return

    if update_failed_vrm:
        shutil.copy(actual_path, expected_path)

    diffs_str = "\n".join(diffs)
    message = (
        f"{what}\n"
        + f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
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
    test(*sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
