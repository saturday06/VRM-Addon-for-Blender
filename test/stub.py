import bpy

print("STUB! Blender=" + bpy.app.version_string)

assert "vrm" in dir(bpy.ops.import_scene)
assert "vrm" in dir(bpy.ops.export_scene)

print("OK")
