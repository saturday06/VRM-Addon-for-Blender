import os

import bpy


def test() -> None:
    os.environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

    repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    vrm_dir = os.path.join(
        os.environ.get(
            "BLENDER_VRM_TEST_RESOURCES_PATH",
            os.path.join(repository_root_dir, "tests", "resources"),
        ),
        "vrm",
    )
    major_minor = os.getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = "template_mesh.vrm"
    expected_path = os.path.join(vrm_dir, major_minor, "out", vrm)
    temp_dir_path = os.path.join(vrm_dir, major_minor, "temp")
    os.makedirs(temp_dir_path, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.icyp.make_basic_armature(WIP_with_template_mesh=True)
    bpy.ops.vrm.model_validate()

    actual_path = os.path.join(temp_dir_path, vrm)
    if os.path.exists(actual_path):
        os.remove(actual_path)
    bpy.ops.export_scene.vrm(filepath=actual_path)

    # TODO:
    actual_size = os.path.getsize(actual_path)
    expected_size = os.path.getsize(expected_path)
    assert (
        abs(actual_size - expected_size) < expected_size / 8
    ), f"actual:{actual_size} != expected:{expected_size}"


if __name__ == "__main__":
    test()
