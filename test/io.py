import os
import pathlib
import sys
import bpy

os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

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
bpy.ops.object.select_all(action="SELECT")
bpy.ops.vrm.model_validate()

actual_out_path = os.path.join(temp_dir_path, os.path.basename(in_path))
bpy.ops.export_scene.vrm(filepath=actual_out_path)
expected_size = os.path.getsize(expected_out_path)
actual_size = os.path.getsize(actual_out_path)
assert expected_size == actual_size, (
    f'"{in_path}" was converted to "{actual_out_path}". The result\'s size {actual_size} is'
    + f'different from "{expected_out_path}"\'s size {expected_size}"'
)
if bpy.app.build_platform != b"Darwin":  # TODO: normals
    assert (  # pylint: disable=W0199
        pathlib.Path(expected_out_path).read_bytes()
        == pathlib.Path(actual_out_path).read_bytes()
    ), (
        f'"{in_path}" was converted to "{actual_out_path}".'
        + f' The result is different from "{expected_out_path}"'
    )

print("OK")
