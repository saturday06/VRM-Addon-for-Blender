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
    "BLENDER_VRM_TEST_VRM_DIR",
    os.path.join(repository_root_dir, "tests", "vrm"),
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
    update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "true"

    vrm, extract_textures_str = sys.argv[sys.argv.index("--") + 1 :]
    in_path = os.path.join(vrm_dir, "in", vrm)

    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    out_vrm_dir = os.path.join(vrm_dir, major_minor, "out")
    out2_vrm_dir = os.path.join(vrm_dir, major_minor, "out2")
    temp_vrm_dir = os.path.join(vrm_dir, major_minor, "temp")
    extract_textures = extract_textures_str == "true"

    if not os.path.exists(os.path.join(out_vrm_dir, vrm)):
        update_vrm_dir = True

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(temp_vrm_dir, vrm + ".blend"))

    assert_import_export(
        in_path,
        os.path.join(out_vrm_dir, vrm),
        temp_vrm_dir,
        extract_textures,
        update_vrm_dir,
    )

    if update_vrm_dir and not os.path.exists(os.path.join(out_vrm_dir, vrm)):
        return

    if not os.path.exists(os.path.join(out2_vrm_dir, vrm)) and not update_vrm_dir:
        assert_import_export(
            os.path.join(out_vrm_dir, vrm),
            os.path.join(out_vrm_dir, vrm),
            temp_vrm_dir,
            extract_textures,
            update_vrm_dir,
        )
        return

    assert_import_export(
        os.path.join(out_vrm_dir, vrm),
        os.path.join(out2_vrm_dir, vrm),
        temp_vrm_dir,
        extract_textures,
        update_vrm_dir,
    )


def assert_import_export(
    in_path: str,
    expected_path: str,
    temp_dir_path: str,
    extract_textures: bool,
    update_vrm_dir: bool,
) -> None:
    bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)

    bpy.ops.import_scene.vrm(
        filepath=in_path,
        extract_textures_into_folder=extract_textures,
        make_new_texture_folder=extract_textures,
    )

    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_dir_path, os.path.basename(in_path))
    bpy.ops.export_scene.vrm(filepath=actual_path)
    actual_bytes = pathlib.Path(actual_path).read_bytes()

    system = platform.system()
    if system == "Darwin":
        float_tolerance = 0.0005
    elif system == "Linux":
        float_tolerance = 0.0006
    else:
        float_tolerance = 0.000001

    if (
        update_vrm_dir
        and in_path != expected_path
        and not vrm_diff(
            actual_bytes, pathlib.Path(in_path).read_bytes(), float_tolerance
        )
    ):
        if os.path.exists(expected_path):
            message = (
                "The input and the output are same. The output file is unnecessary.\n"
                + f"input ={in_path}\n"
                + f"output={expected_path}\n"
            )
            if platform.system() == "Windows":
                sys.stderr.buffer.write(message.encode())
                raise AssertionError
            raise AssertionError(message)
        sys.exit(0)

    if not os.path.exists(expected_path):
        shutil.copy(actual_path, expected_path)

    diffs = vrm_diff(
        actual_bytes,
        pathlib.Path(expected_path).read_bytes(),
        float_tolerance,
    )
    if not diffs:
        return

    if update_vrm_dir:
        shutil.copy(actual_path, expected_path)

    diffs_str = "\n".join(diffs[:50])
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
