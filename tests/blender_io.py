import os
import pathlib
import shutil
import sys

import bpy

os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "true"

in_path, expected_out_path, temp_dir_path = sys.argv[sys.argv.index("--") + 1 :]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

bpy.ops.import_scene.vrm(
    filepath=in_path,
    # Same as __init__.py menu_import(self, context) for now
    is_put_spring_bone_info=True,
    import_normal=True,
    remove_doubles=False,
    set_bone_roll=True,
)
# bpy.ops.object.select_all(action="SELECT")
bpy.ops.vrm.model_validate()

actual_out_path = os.path.join(temp_dir_path, os.path.basename(in_path))
bpy.ops.export_scene.vrm(filepath=actual_out_path)
actual_size = os.path.getsize(actual_out_path)
actual_bytes = pathlib.Path(actual_out_path).read_bytes()

if (
    update_vrm_dir
    and actual_size == os.path.getsize(in_path)
    and actual_bytes == pathlib.Path(in_path).read_bytes()
):
    sys.exit(0)

try:
    expected_size = os.path.getsize(expected_out_path)
    assert (
        expected_size == actual_size
    ), f"""Unexpected VRM Output Size
  Input: {in_path}
  Expected Output: {expected_out_path}
  Expected Size: {expected_size}
  Actual Output: {actual_out_path}
  Actual Size: {actual_size}"""
    if bpy.app.build_platform != b"Darwin":  # TODO: normals
        expected_bytes = pathlib.Path(expected_out_path).read_bytes()
        assert (  # pylint: disable=W0199
            expected_bytes == actual_bytes
        ), f"""Unexpected VRM Binary
  Input: {in_path}
  Expected Output: {expected_out_path}
  Actual Output: {actual_out_path}"""
except FileNotFoundError:
    if update_vrm_dir:
        shutil.copy(actual_out_path, expected_out_path)
    raise
except AssertionError:
    if update_vrm_dir:
        shutil.copy(actual_out_path, expected_out_path)
    raise
