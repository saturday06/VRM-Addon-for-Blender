# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import os
import sys
from os import environ
from pathlib import Path

from io_scene_vrm.common import ops

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
resources_dir = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(repository_root_dir / "tests" / "resources"),
    )
)
vrm_dir = resources_dir / "vrm" / "broken"


def get_test_command_args() -> list[list[str]]:
    names = [blend_path.name for blend_path in vrm_dir.glob("*.vrm")]
    command_args: list[list[str]] = [[name] for name in sorted(dict.fromkeys(names))]
    return command_args


def test(vrm: str) -> None:
    if (
        vrm == "draco.vrm"
        and os.getenv("BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS") == "yes"
    ):
        # Ubuntu 24.04はdracoを読もうとすると例外が発生する
        return

    in_path = vrm_dir / vrm
    assert ops.import_scene.vrm(filepath=str(in_path)) == {"FINISHED"}


if __name__ == "__main__":
    test(*sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
