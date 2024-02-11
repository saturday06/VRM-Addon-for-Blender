import shutil
import sys
from os import environ, getenv
from pathlib import Path

import bpy

from io_scene_vrm.common.logging import get_logger
from io_scene_vrm.importer.vrm_diff import vrm_diff

logger = get_logger(__name__)

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
vrm_dir = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(repository_root_dir / "tests" / "resources"),
    ),
    "vrm",
)


def get_test_command_args() -> list[list[str]]:
    command_args: list[list[str]] = []
    for vrm, extract_textures in [
        (v, e)
        for e in ["false", "true"]
        for v in sorted((vrm_dir / "in").iterdir())
        if v.suffix == ".vrm"
    ]:
        command_args.append([str(vrm.name), extract_textures])
    return command_args


def test(vrm: str, extract_textures_str: str) -> None:
    environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
    update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"

    in_path = vrm_dir / "in" / vrm

    major_minor = getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    out_vrm_dir = vrm_dir / major_minor / "out"
    temp_vrm_dir = vrm_dir / major_minor / "temp"
    temp_vrm_dir.mkdir(parents=True, exist_ok=True)
    extract_textures = extract_textures_str == "true"

    if not (out_vrm_dir / vrm).exists():
        update_failed_vrm = True

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.import_scene.vrm(
        filepath=str(in_path),
        extract_textures_into_folder=extract_textures,
        make_new_texture_folder=extract_textures,
    )

    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    actual_path = temp_vrm_dir / (
        f"test_import_export.{extract_textures}." + in_path.name
    )
    if actual_path.exists():
        actual_path.unlink()

    bpy.ops.export_scene.vrm(filepath=str(actual_path))
    actual_bytes = actual_path.read_bytes()

    float_tolerance = 0.00055

    expected_path = out_vrm_dir / vrm
    if not expected_path.exists():
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(actual_path, expected_path)

    diffs = vrm_diff(
        actual_bytes,
        expected_path.read_bytes(),
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
    if sys.platform == "win32":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test(*sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
