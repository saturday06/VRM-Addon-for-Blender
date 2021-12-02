import os
from typing import Any

import bpy


def add_shaders(self: Any) -> None:
    filedir = os.path.join(os.path.dirname(__file__), "material_node_groups.blend")
    with bpy.data.libraries.load(filedir, link=False) as (data_from, data_to):
        for nt in data_from.node_groups:
            if nt not in bpy.data.node_groups:
                data_to.node_groups.append(nt)


def shader_node_group_import(shader_node_group_name: str) -> None:
    if shader_node_group_name in bpy.data.node_groups:
        return
    filedir = os.path.join(
        os.path.dirname(__file__),
        "material_node_groups.blend",
        "NodeTree",
    )
    filepath = os.path.join(filedir, shader_node_group_name)
    bpy.ops.wm.append(
        filepath=filepath,
        filename=shader_node_group_name,
        directory=filedir,
    )
