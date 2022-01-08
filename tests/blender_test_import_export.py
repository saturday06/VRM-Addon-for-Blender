import os
import pathlib
import platform
import shutil
import sys
from typing import List, Optional

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.vrm_diff import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;

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
    out2_vrm_dir = os.path.join(vrm_dir, major_minor, "out2")
    temp_vrm_dir = os.path.join(vrm_dir, major_minor, "temp")
    os.makedirs(temp_vrm_dir, exist_ok=True)
    test_blend_path = os.path.join(
        os.path.dirname(vrm_dir),
        "blend",
        major_minor,
        os.path.splitext(vrm)[0] + ".blend",
    )
    extract_textures = extract_textures_str == "true"

    if not os.path.exists(os.path.join(out_vrm_dir, vrm)):
        update_failed_vrm = True

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])
    startup_blend_path = os.path.join(temp_vrm_dir, vrm + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=startup_blend_path)

    assert_import_export(
        in_path,
        os.path.join(out_vrm_dir, vrm),
        temp_vrm_dir,
        extract_textures,
        update_failed_vrm,
        startup_blend_path,
        test_blend_path,
    )

    if update_failed_vrm and not os.path.exists(os.path.join(out_vrm_dir, vrm)):
        return

    if os.path.exists(os.path.join(out2_vrm_dir, vrm + ".TO_BE_SUPPORTED.txt")):
        print(f"WARNING: Second import-export assertion for {vrm} is skipped.")
        return

    if not os.path.exists(os.path.join(out2_vrm_dir, vrm)) and not update_failed_vrm:
        assert_import_export(
            os.path.join(out_vrm_dir, vrm),
            os.path.join(out_vrm_dir, vrm),
            temp_vrm_dir,
            extract_textures,
            update_failed_vrm,
            startup_blend_path,
        )
        return

    assert_import_export(
        os.path.join(out_vrm_dir, vrm),
        os.path.join(out2_vrm_dir, vrm),
        temp_vrm_dir,
        extract_textures,
        update_failed_vrm,
        startup_blend_path,
    )


def assert_import_export(
    in_path: str,
    expected_path: str,
    temp_dir_path: str,
    extract_textures: bool,
    update_failed_vrm: bool,
    startup_blend_path: str,
    test_blend_path: Optional[str] = None,
) -> None:
    bpy.ops.wm.open_mainfile(filepath=startup_blend_path)

    bpy.ops.import_scene.vrm(
        filepath=in_path,
        extract_textures_into_folder=extract_textures,
        make_new_texture_folder=extract_textures,
    )

    bpy.ops.vrm.model_validate()

    if (
        not extract_textures
        and test_blend_path is not None
        and not os.path.exists(test_blend_path)
        and not os.path.exists(test_blend_path + ".OPT_OUT.txt")
    ):
        os.makedirs(os.path.dirname(test_blend_path), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=test_blend_path)

    actual_path = os.path.join(temp_dir_path, os.path.basename(in_path))
    if os.path.exists(actual_path):
        os.remove(actual_path)
    bpy.ops.export_scene.vrm(filepath=actual_path)
    actual_bytes = pathlib.Path(actual_path).read_bytes()

    system = platform.system()
    if system in ["Darwin", "Linux"]:
        float_tolerance = 0.00055
    else:
        float_tolerance = 0.000015

    if (
        update_failed_vrm
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
            sys.stderr.buffer.write(message.encode())
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
