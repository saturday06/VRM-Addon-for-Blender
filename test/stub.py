import bpy
import os
import tempfile

print("STUB! Blender=" + bpy.app.version_string)

assert "vrm" in dir(bpy.ops.import_scene)
assert "vrm" in dir(bpy.ops.export_scene)

bpy.ops.icyp.make_basic_armature()
bpy.ops.vrm.model_validate()

with tempfile.TemporaryDirectory() as temp_dir:
    filepath = os.path.join(temp_dir, "out.vrm")
    bpy.ops.export_scene.vrm(filepath=filepath)
    assert os.path.getsize(filepath) > 0

print("OK")
