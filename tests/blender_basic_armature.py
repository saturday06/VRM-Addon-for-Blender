import os
import pathlib
import sys

import bpy

os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

expected_out_path, temp_dir_path = sys.argv[sys.argv.index("--") + 1 :]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

bpy.ops.icyp.make_basic_armature()
bpy.ops.vrm.model_validate()

filepath = os.path.join(temp_dir_path, "basic_armature.vrm")
bpy.ops.export_scene.vrm(filepath=filepath)
assert os.path.getsize(filepath) > 0
assert (
    pathlib.Path(filepath).read_bytes() == pathlib.Path(expected_out_path).read_bytes()
)
