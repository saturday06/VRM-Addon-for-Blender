from pathlib import Path

import bpy
from bpy.types import Context

from io_scene_vrm.common.native import read_blend_method_from_memory_address


def test(context: Context) -> None:
    bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).parent / "blend_mode.blend"))

    for material_name, expected_blend_method in {
        "Opaque": "OPAQUE",
        "AlphaClip": "CLIP",
        "AlphaHashed": "HASHED",
        "AlphaBlend": "BLEND",
    }.items():
        material = context.blend_data.materials[material_name]
        actual_blend_method = read_blend_method_from_memory_address(material)
        assert expected_blend_method == actual_blend_method, (
            f'"{material_name}" material is not "{expected_blend_method}"'
            + f" but {actual_blend_method}"
        )


if __name__ == "__main__":
    test(bpy.context)
