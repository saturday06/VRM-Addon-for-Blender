from os import environ, getenv
from pathlib import Path

import bpy


def test() -> None:
    environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

    repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
    vrm_dir = Path(
        environ.get(
            "BLENDER_VRM_TEST_RESOURCES_PATH",
            str(repository_root_dir / "tests" / "resources"),
        ),
        "vrm",
    )
    major_minor = getenv("BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION") or "unversioned"
    vrm = "template_mesh.vrm"
    expected_path = vrm_dir / major_minor / "out" / vrm
    if not expected_path.exists():
        message = f"No expected result file: {expected_path}"
        raise FileNotFoundError(message)
    temp_dir_path = vrm_dir / major_minor / "temp"
    temp_dir_path.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.icyp.make_basic_armature(WIP_with_template_mesh=True)
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    actual_path = temp_dir_path / vrm
    if actual_path.exists():
        actual_path.unlink()
    bpy.ops.export_scene.vrm(filepath=str(actual_path))

    # TODO: compare bin
    actual_size = actual_path.stat().st_size
    expected_size = expected_path.stat().st_size
    assert (
        abs(actual_size - expected_size) < expected_size / 8
    ), f"actual:{actual_size} != expected:{expected_size}"


if __name__ == "__main__":
    test()
