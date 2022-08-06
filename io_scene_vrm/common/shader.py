from collections import abc
from os.path import dirname, join
from typing import Any, List, Optional, Tuple

import bgl
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


def get_image_name_and_sampler_type(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[Tuple[str, int, int]]:
    if (
        input_socket_name == "NormalmapTexture"
        and "NormalmapTexture" not in shader_node.inputs
        and "NomalmapTexture" in shader_node.inputs
    ):
        input_socket_name = "NomalmapTexture"

    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    links = socket.links
    if not links:
        return None

    from_node = links[0].from_node
    if not from_node:
        return None

    image = from_node.image
    if not image:
        return None

    image_name = image.name
    if not image_name:
        return None

    # blender is ('Linear', 'Closest', 'Cubic', 'Smart') glTF is Linear, Closest
    if from_node.interpolation == "Closest":
        filter_type = bgl.GL_NEAREST
    else:
        filter_type = bgl.GL_LINEAR

    # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
    if from_node.extension == "REPEAT":
        wrap_type = bgl.GL_REPEAT
    else:
        wrap_type = bgl.GL_CLAMP_TO_EDGE

    return image_name, wrap_type, filter_type


def float_or_none(v: Any) -> Optional[float]:
    if isinstance(v, (float, int)):
        return float(v)
    return None


def get_float_value(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[float]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = float_or_none(socket.default_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return float_or_none(outputs[0].default_value)


def rgba_or_none(vs: Any) -> Optional[List[float]]:
    if not isinstance(vs, abc.Iterable):
        return None

    rgba = []
    for v in vs:
        f = float_or_none(v)
        if f is None:
            return None
        rgba.append(f)
        if len(rgba) > 4:
            return None

    if len(rgba) == 3:
        rgba.append(1.0)
    if len(rgba) != 4:
        return None

    return rgba


def get_rgba_val(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[List[float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgba_or_none(socket.default_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgba_or_none(outputs[0].default_value)


def rgb_or_none(vs: Any) -> Optional[List[float]]:
    if not isinstance(vs, abc.Iterable):
        return None

    rgb = []
    for v in vs:
        f = float_or_none(v)
        if f is None:
            return None
        rgb.append(f)
        if len(rgb) > 4:
            return None

    if len(rgb) == 4:
        rgb.pop()
    if len(rgb) != 3:
        return None

    return rgb


def get_rgb_val(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[List[float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgba_or_none(socket.default_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgb_or_none(outputs[0].default_value)
