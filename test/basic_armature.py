import bpy
import os
import tempfile
import pathlib

bpy.ops.icyp.make_basic_armature()
bpy.data.objects["skeleton"].select_set(True)
bpy.ops.vrm.model_validate()

with tempfile.TemporaryDirectory() as temp_dir:
    filepath = os.path.join(temp_dir, "basic_armature.vrm")
    bpy.ops.export_scene.vrm(filepath=filepath)
    assert os.path.getsize(filepath) > 0

    assert "skeleton" in bpy.data.objects
    bpy.ops.wm.read_factory_settings()
    assert "skeleton" not in bpy.data.objects

    bpy.ops.import_scene.vrm(filepath=filepath)
    bpy.data.objects["skeleton"].select_set(True)
    filepath2 = os.path.join(temp_dir, "basic_armature.vrm")
    bpy.ops.export_scene.vrm(filepath=filepath2)
    assert os.path.getsize(filepath2) > 0

    assert pathlib.Path(filepath).read_bytes() == pathlib.Path(filepath2).read_bytes()

print("OK")
