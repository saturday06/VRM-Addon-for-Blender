import json
import math
import struct
from sys import float_info
from typing import Any, Dict, List, Sequence, Tuple

import bpy


def pack_glb(json_dict: Dict[str, Any], binary_chunk: bytes) -> bytes:
    magic = b"glTF" + struct.pack("<I", 2)
    json_str = json.dumps(json_dict).encode("utf-8")
    if len(json_str) % 4 != 0:
        json_str += b"\x20" * (4 - len(json_str) % 4)
    json_size = struct.pack("<I", len(json_str))
    if len(binary_chunk) % 4 != 0:
        binary_chunk += b"\x00" * (4 - len(binary_chunk) % 4)
    bin_size = struct.pack("<I", len(binary_chunk))
    total_size = struct.pack(
        "<I", len(json_str) + len(binary_chunk) + 28
    )  # include header size
    return (
        magic
        + total_size
        + json_size
        + b"JSON"
        + json_str
        + bin_size
        + b"BIN\x00"
        + binary_chunk
    )


def normalize_weights_compatible_with_gl_float(
    weights: Sequence[float],
) -> Sequence[float]:
    if abs(sum(weights) - 1.0) < float_info.epsilon:
        return weights

    def to_gl_float(array4: Sequence[float]) -> Sequence[float]:
        return list(struct.unpack("<ffff", struct.pack("<ffff", *array4)))

    # Simulate export and import
    weights = to_gl_float(weights)
    for _ in range(10):
        next_weights = to_gl_float([weights[i] / sum(weights) for i in range(4)])
        error = abs(1 - math.fsum(weights))
        next_error = abs(1 - math.fsum(next_weights))
        if error >= float_info.epsilon and error > next_error:
            weights = next_weights
        else:
            break

    return weights


def shader_nodes_and_materials(
    used_materials: List[bpy.types.Material],
) -> List[Tuple[bpy.types.Node, bpy.types.Material]]:
    return [
        (node.inputs["Surface"].links[0].from_node, mat)
        for mat in used_materials
        if mat.node_tree is not None
        for node in mat.node_tree.nodes
        if node.type == "OUTPUT_MATERIAL"
        and node.inputs["Surface"].links
        and node.inputs["Surface"].links[0].from_node.type == "GROUP"
        and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER")
        is not None
    ]
