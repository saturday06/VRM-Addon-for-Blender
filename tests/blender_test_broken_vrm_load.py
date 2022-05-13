import os
import pathlib
import sys
from typing import List

import bpy

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
resources_dir = os.environ.get(
    "BLENDER_VRM_TEST_RESOURCES_PATH",
    os.path.join(repository_root_dir, "tests", "resources"),
)
vrm_dir = os.path.join(resources_dir, "vrm", "broken")


def get_test_command_args() -> List[List[str]]:
    names = [blend_path.name for blend_path in pathlib.Path(vrm_dir).glob("*.vrm")]
    command_args: List[List[str]] = [
        [name] for name in sorted(list(dict.fromkeys(names)))
    ]
    return command_args


def test() -> None:
    vrm = sys.argv[sys.argv.index("--") + 1]

    if bpy.app.version < (2, 93) and vrm == "draco.vrm":
        return

    in_path = os.path.join(vrm_dir, vrm)
    assert bpy.ops.import_scene.vrm(filepath=in_path) == {"FINISHED"}


if __name__ == "__main__":
    test()
