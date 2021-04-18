import os
import pathlib
import platform
import shutil
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;


def fix_stderr_encoding() -> None:
    if platform.system() == "Windows":
        sys.stderr.reconfigure(encoding="ansi")  # type: ignore


os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "true"

in_path, expected_out_path, temp_dir_path, extract_textures_str = sys.argv[
    sys.argv.index("--") + 1 :
]
extract_textures = extract_textures_str == "true"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

if in_path.endswith(".vrm"):
    bpy.ops.import_scene.vrm(
        filepath=in_path,
        extract_textures_into_folder=extract_textures,
        make_new_texture_folder=extract_textures,
    )
elif in_path.endswith(".blend"):
    bpy.ops.wm.open_mainfile(filepath=in_path)

# bpy.ops.object.select_all(action="SELECT")
bpy.ops.vrm.model_validate()

actual_out_path = os.path.join(temp_dir_path, os.path.basename(in_path))
bpy.ops.export_scene.vrm(filepath=actual_out_path)
actual_out_bytes = pathlib.Path(actual_out_path).read_bytes()

system = platform.system()
if system == "Darwin":
    float_tolerance = 0.0005
elif system == "Linux":
    float_tolerance = 0.0006
else:
    float_tolerance = 0.000001

if (
    update_vrm_dir
    and in_path.endswith(".vrm")
    and in_path != expected_out_path
    and not vrm_diff(
        actual_out_bytes, pathlib.Path(in_path).read_bytes(), float_tolerance
    )
):
    if os.path.exists(expected_out_path):
        fix_stderr_encoding()
        raise Exception(
            f"""The input and the output are same. The output file is unnecessary.
input ={in_path}
output={expected_out_path}
"""
        )
    sys.exit(0)

try:
    diffs = vrm_diff(
        actual_out_bytes, pathlib.Path(expected_out_path).read_bytes(), float_tolerance
    )
except FileNotFoundError:
    if update_vrm_dir:
        shutil.copy(actual_out_path, expected_out_path)
    fix_stderr_encoding()
    raise

diffs_str = "\n".join(diffs[:50])

try:
    assert (
        len(diffs) == 0
    ), f"""Exceeded the VRM diff threshold:{float_tolerance:19.17f}
left ={actual_out_path}
right={expected_out_path}
{diffs_str}"""
except AssertionError:
    if update_vrm_dir:
        shutil.copy(actual_out_path, expected_out_path)
    fix_stderr_encoding()
    raise
