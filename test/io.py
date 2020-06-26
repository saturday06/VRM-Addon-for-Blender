import bpy
import os
import tempfile
import sys
import pathlib

args = list(sys.argv)
while args.pop(0) != "--":
    pass
in_path = args[0]

os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

bpy.ops.import_scene.vrm(filepath=in_path)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.vrm.model_validate()

with tempfile.TemporaryDirectory() as temp_dir:
    out_path = os.path.join(temp_dir, "out.vrm")
    bpy.ops.export_scene.vrm(filepath=out_path)
    assert os.path.getsize(in_path) == os.path.getsize(out_path)
    if bpy.app.build_platform != b"Darwin":  # TODO: normals
        assert pathlib.Path(in_path).read_bytes() == pathlib.Path(out_path).read_bytes()

print("OK")
