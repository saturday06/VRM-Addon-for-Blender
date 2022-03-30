from os.path import dirname, join

import bpy

__file_names = [
    "mtoon_unversioned.blend",
    "transparent_z_write.blend",
    "gltf.blend",
]


def add_shaders() -> None:
    for file_name in __file_names:
        path = join(dirname(__file__), file_name)
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            for node_group in data_from.node_groups:
                if node_group not in bpy.data.node_groups:
                    data_to.node_groups.append(node_group)


def shader_node_group_import(shader_node_group_name: str) -> None:
    if shader_node_group_name in bpy.data.node_groups:
        return
    for file_name in __file_names:
        path = join(
            dirname(__file__),
            file_name,
            "NodeTree",
        )
        bpy.ops.wm.append(
            filepath=join(path, shader_node_group_name),
            filename=shader_node_group_name,
            directory=path,
        )
