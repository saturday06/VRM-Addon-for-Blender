#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import logging
import math
import struct
import sys
from pathlib import Path

from io_scene_vrm.common.deep import Json, make_json
from io_scene_vrm.common.gl import GL_FLOAT
from io_scene_vrm.common.gltf import pack_glb, parse_glb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        json_dict: dict[str, Json] = {
            "asset": {
                "version": "2.0",
                "generator": "io-scene-vrm-model-generator.py",
            },
        }
        binary_chunk = b""
        output_path = Path(__file__).parent.parent / "tests" / "temp" / "generated.vrm"
    else:
        input_path = Path(argv[1])
        read_bytes = input_path.read_bytes()
        json_dict, binary_chunk = parse_glb(read_bytes)
        output_path = input_path.with_suffix(".gen.vrm")

    enable_vertex_color = False

    buffer_dicts = json_dict.get("buffers")
    if not isinstance(buffer_dicts, list):
        buffer_dicts = []
        json_dict["buffers"] = buffer_dicts

    # position_buffer_index = len(json_dict["buffers"])
    position_buffer_byte_offset = len(binary_chunk)
    positions: list[tuple[float, float, float]] = [
        (-0.1, 0.0, 0.1),
        (0.1, 0.0, 0.1),
        (0.0, 0.1, 0.0),
        # --
        (0.0, 0.1, 0.0),
        (-0.1, 0.0, -0.1),
        (-0.1, 0.0, 0.1),
        # --
        (0.0, 0.1, 0.0),
        (0.1, 0.0, -0.1),
        (-0.1, 0.0, -0.1),
        # --
        (0.1, 0.0, 0.1),
        (0.1, 0.0, -0.1),
        (0.0, 0.1, 0.0),
        # --
        (0.0, -0.1, 0.0),
        (0.1, 0.0, 0.1),
        (-0.1, 0.0, 0.1),
        # --
        (-0.1, 0.0, 0.1),
        (-0.1, 0.0, -0.1),
        (0.0, -0.1, 0.0),
        # --
        (-0.1, 0.0, -0.1),
        (0.1, 0.0, -0.1),
        (0.0, -0.1, 0.0),
        # --
        (0.0, -0.1, 0.0),
        (0.1, 0.0, -0.1),
        (0.1, 0.0, 0.1),
    ]

    flat_positions = sum(positions, ())
    position_buffer_bytes = struct.pack(f"<{len(flat_positions)}f", *flat_positions)
    binary_chunk += position_buffer_bytes
    # json_dict["buffers"].append(
    #    {
    #        "uri": "data:application/gltf-buffer;base64,"
    #        + base64.b64encode(position_buffer_bytes).decode("ascii"),
    #        "byteLength": len(position_buffer_bytes),
    #    }
    # )

    texcoord_buffer_byte_offset = len(binary_chunk)
    texcoords: list[tuple[float, float]] = [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        # --
    ]
    if len(texcoords) != len(positions):
        raise AssertionError
    flat_texcoords = sum(texcoords, ())
    if len(flat_texcoords) != len(flat_positions) / 3 * 2:
        raise AssertionError
    texcoord_buffer_bytes = struct.pack(f"<{len(flat_texcoords)}f", *flat_texcoords)
    binary_chunk += texcoord_buffer_bytes

    color_buffer_byte_offset = None
    color_buffer_bytes = None
    color_buffer_view_index = None
    colors = None
    if enable_vertex_color:
        # color_buffer_index = len(json_dict["buffers"])
        color_buffer_byte_offset = len(binary_chunk)
        colors = [
            tuple(0.0 if c <= 0 else 1.0 for c in position) for position in positions
        ]

        if len(colors) != len(positions):
            raise AssertionError
        flat_colors = sum(colors, ())
        if len(flat_colors) != len(flat_positions):
            raise AssertionError
        color_buffer_bytes = struct.pack(f"<{len(flat_colors)}f", *flat_colors)
        binary_chunk += color_buffer_bytes
        # json_dict["buffers"].append(
        #    {
        #        "uri": "data:application/gltf-buffer;base64,"
        #        + base64.b64encode(color_buffer_bytes).decode("ascii"),
        #        "byteLength": len(color_buffer_bytes),
        #    }
        # )

    buffer_view_dicts = json_dict.get("bufferViews")
    if not isinstance(buffer_view_dicts, list):
        buffer_view_dicts = []
        json_dict["bufferViews"] = buffer_view_dicts
    position_buffer_view_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": position_buffer_byte_offset,
            "byteLength": len(position_buffer_bytes),
            "target": 34962,  # ARRAY_BUFFER
        }
    )
    texcoord_buffer_view_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": texcoord_buffer_byte_offset,
            "byteLength": len(texcoord_buffer_bytes),
            "target": 34962,  # ARRAY_BUFFER
        }
    )

    if color_buffer_byte_offset is not None and color_buffer_bytes is not None:
        color_buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": color_buffer_byte_offset,
                "byteLength": len(color_buffer_bytes),
                "target": 34962,  # ARRAY_BUFFER
            }
        )

    accessor_dicts = json_dict.get("accessors")
    if not isinstance(accessor_dicts, list):
        accessor_dicts = []
        json_dict["accessors"] = accessor_dicts
    position_accessors_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": position_buffer_view_index,
            "byteOffset": 0,
            "type": "VEC3",
            "componentType": GL_FLOAT,
            "count": len(positions),
            "min": [-0.1, -0.1, -0.1],
            "max": [0.1, 0.1, 0.1],
        }
    )
    texcoord_accessors_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": texcoord_buffer_view_index,
            "byteOffset": 0,
            "type": "VEC2",
            "componentType": GL_FLOAT,
            "count": len(texcoords),
            "min": [0.0, 0.0],
            "max": [1.0, 1.0],
        }
    )

    image_bytes = Path(__file__).with_name("model_generator_texture.png").read_bytes()
    padded_image_bytes = bytes(image_bytes)
    while len(padded_image_bytes) % 16 == 0:
        padded_image_bytes += b"\x00"
    image_buffer_byte_offset = len(binary_chunk)
    binary_chunk += padded_image_bytes
    image_buffer_view_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": image_buffer_byte_offset,
            "byteLength": len(image_bytes),
        }
    )

    sampler_dicts = json_dict.get("samplers")
    if not isinstance(sampler_dicts, list):
        sampler_dicts = []
        json_dict["samplers"] = sampler_dicts
    image_sampler_index = len(sampler_dicts)
    sampler_dicts.append(
        {"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}
    )

    image_dicts = json_dict.get("images")
    if not isinstance(image_dicts, list):
        image_dicts = []
        json_dict["images"] = image_dicts

    image_index = len(image_dicts)
    image_dicts.append(
        {
            "bufferView": image_buffer_view_index,
            "mimeType": "image/png",
        }
    )

    texture_dicts = json_dict.get("textures")
    if not isinstance(texture_dicts, list):
        texture_dicts = []
        json_dict["textures"] = texture_dicts
    texture_index = len(texture_dicts)
    texture_dicts.append(
        {
            "sampler": image_sampler_index,
            "source": image_index,
        }
    )
    # Second texture (same image) used for KHR_character_expression_texture demo
    texture_index_2 = len(texture_dicts)
    texture_dicts.append(
        {
            "sampler": image_sampler_index,
            "source": image_index,
        }
    )

    material_dicts = json_dict.get("materials")
    if not isinstance(material_dicts, list):
        material_dicts = []
        json_dict["materials"] = material_dicts
    material_index = len(material_dicts)
    material_dicts.append(
        {
            "pbrMetallicRoughness": {"baseColorTexture": {"index": texture_index}},
            "emissiveFactor": [0.2, 0.2, 0.2],
        }
    )

    if color_buffer_view_index is not None and colors is not None:
        color_accessors_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": color_buffer_view_index,
                "byteOffset": 0,
                "type": "VEC3",
                "componentType": GL_FLOAT,
                "count": len(colors),
                "min": [0.0, 0.0, 0.0],
                "max": [1.0, 1.0, 1.0],
            }
        )
        primitive = {
            "attributes": {
                "POSITION": position_accessors_index,
                "COLOR_0": color_accessors_index,
                "TEXCOORD_0": texcoord_accessors_index,
            },
            "material": material_index,
        }
    else:
        primitive = {
            "attributes": {
                "POSITION": position_accessors_index,
                "TEXCOORD_0": texcoord_accessors_index,
            },
            "material": material_index,
        }

    mesh_dicts = json_dict.get("meshes")
    if not isinstance(mesh_dicts, list):
        mesh_dicts = list[Json]()
        json_dict["meshes"] = mesh_dicts
    mesh_index = len(mesh_dicts)
    mesh_dicts.append(make_json({"primitives": [primitive]}))

    node_dicts = json_dict.get("nodes")
    if not isinstance(node_dicts, list):
        node_dicts = []
        json_dict["nodes"] = node_dicts

    human_bones_dict = {}

    hips_index = len(node_dicts)
    spine_index = len(node_dicts) + 1
    head_index = len(node_dicts) + 2

    left_upper_leg_index = len(node_dicts) + 3
    left_lower_leg_index = len(node_dicts) + 4
    left_foot_index = len(node_dicts) + 5
    left_upper_arm_index = len(node_dicts) + 6
    left_lower_arm_index = len(node_dicts) + 7
    left_hand_index = len(node_dicts) + 8

    right_upper_leg_index = len(node_dicts) + 9
    right_lower_leg_index = len(node_dicts) + 10
    right_foot_index = len(node_dicts) + 11
    right_upper_arm_index = len(node_dicts) + 12
    right_lower_arm_index = len(node_dicts) + 13
    right_hand_index = len(node_dicts) + 14

    node_dicts.extend(
        [
            {
                "name": "hips",
                "children": [
                    spine_index,
                    left_upper_leg_index,
                    right_upper_leg_index,
                ],
                "translation": [0, 0.5, 0],
            },
            {
                "name": "spine",
                "children": [head_index, left_upper_arm_index, right_upper_arm_index],
                "translation": [0, 0.25, 0],
                "mesh": mesh_index,
            },
            {"name": "head", "translation": [0, 0.5, 0]},
            {
                "name": "leftUpperLeg",
                "children": [left_lower_leg_index],
                "translation": [0.125, 0, 0],
                "mesh": mesh_index,
            },
            {
                "name": "leftLowerLeg",
                "children": [left_foot_index],
                "translation": [0, -0.25, 0],
                "mesh": mesh_index,
            },
            {"name": "leftFoot", "translation": [0, -0.25, 0], "mesh": mesh_index},
            {
                "name": "leftUpperArm",
                "children": [left_lower_arm_index],
                "translation": [0.25, 0.25, 0],
                "mesh": mesh_index,
            },
            {
                "name": "leftLowerArm",
                "children": [left_hand_index],
                "translation": [0.25, 0, 0],
                "mesh": mesh_index,
            },
            {"name": "leftHand", "translation": [0.25, 0, 0], "mesh": mesh_index},
            {
                "name": "rightUpperLeg",
                "children": [right_lower_leg_index],
                "translation": [-0.125, 0, 0],
                "mesh": mesh_index,
            },
            {
                "name": "rightLowerLeg",
                "children": [right_foot_index],
                "translation": [0, -0.25, 0],
                "mesh": mesh_index,
            },
            {"name": "rightFoot", "translation": [0, -0.25, 0], "mesh": mesh_index},
            {
                "name": "rightUpperArm",
                "children": [right_lower_arm_index],
                "translation": [-0.25, 0.25, 0],
                "mesh": mesh_index,
            },
            {
                "name": "rightLowerArm",
                "children": [right_hand_index],
                "translation": [-0.25, 0, 0],
                "mesh": mesh_index,
            },
            {"name": "rightHand", "translation": [-0.25, 0, 0], "mesh": mesh_index},
        ]
    )

    scene_dicts = json_dict.get("scenes")
    if not isinstance(scene_dicts, list):
        scene_dicts = []
        json_dict["scenes"] = scene_dicts

    human_bones_dict = {
        "hips": {"node": hips_index},
        "spine": {"node": spine_index},
        "head": {"node": head_index},
        "leftUpperLeg": {"node": left_upper_leg_index},
        "leftLowerLeg": {"node": left_lower_leg_index},
        "leftFoot": {"node": left_foot_index},
        "rightUpperLeg": {"node": right_upper_leg_index},
        "rightLowerLeg": {"node": right_lower_leg_index},
        "rightFoot": {"node": right_foot_index},
        "leftUpperArm": {"node": left_upper_arm_index},
        "leftLowerArm": {"node": left_lower_arm_index},
        "leftHand": {"node": left_hand_index},
        "rightUpperArm": {"node": right_upper_arm_index},
        "rightLowerArm": {"node": right_lower_arm_index},
        "rightHand": {"node": right_hand_index},
    }

    # --- Morph targets for KHR_character_expression ---
    # Four facial expressions driven by morph targets
    morph_expressions = ["happy", "angry", "blink", "jawOpen"]
    # Position deltas for each morph target (24 vertices)
    morph_target_deltas: list[list[tuple[float, float, float]]] = [
        # happy: upper vertices move up
        [(0.0, 0.02, 0.0) if pos[1] > 0.0 else (0.0, 0.0, 0.0) for pos in positions],
        # angry: upper vertices compress inward
        [
            (pos[0] * -0.2, -0.01, 0.0) if pos[1] > 0.0 else (0.0, 0.0, 0.0)
            for pos in positions
        ],
        # blink: near-equator vertices close inward
        [
            (0.0, -0.02, 0.0) if abs(pos[1]) < 0.05 else (0.0, 0.0, 0.0)
            for pos in positions
        ],
        # jawOpen: lower vertices move down
        [(0.0, -0.02, 0.0) if pos[1] < 0.0 else (0.0, 0.0, 0.0) for pos in positions],
    ]
    morph_target_accessor_indices = list[int]()
    for deltas in morph_target_deltas:
        morph_byte_offset = len(binary_chunk)
        flat_deltas = sum(deltas, ())
        morph_bytes = struct.pack(f"<{len(flat_deltas)}f", *flat_deltas)
        binary_chunk += morph_bytes
        morph_bv_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": morph_byte_offset,
                "byteLength": len(morph_bytes),
                "target": 34962,  # ARRAY_BUFFER
            }
        )
        morph_acc_index = len(accessor_dicts)
        morph_target_accessor_indices.append(morph_acc_index)
        accessor_dicts.append(
            {
                "bufferView": morph_bv_index,
                "byteOffset": 0,
                "type": "VEC3",
                "componentType": GL_FLOAT,
                "count": len(positions),
            }
        )

    # Add morph targets to the mesh primitive and set targetNames in extras
    mesh_dict = mesh_dicts[mesh_index]
    if isinstance(mesh_dict, dict):
        primitives_list = mesh_dict.get("primitives")
        if isinstance(primitives_list, list) and primitives_list:
            prim_dict = primitives_list[0]
            if isinstance(prim_dict, dict):
                prim_dict["targets"] = [
                    {"POSITION": morph_target_accessor_indices[i]}
                    for i in range(len(morph_expressions))
                ]
        mesh_dict["extras"] = make_json({"targetNames": morph_expressions})

    # Set initial morph target weights on the spine node
    spine_node_dict = node_dicts[spine_index]
    if isinstance(spine_node_dict, dict):
        spine_node_dict["weights"] = make_json([0.0] * len(morph_expressions))

    # --- Shared animation accessors ---
    # Time accessor for 2-keyframe animations: t=0.0 and t=1.0
    expr_time_byte_offset = len(binary_chunk)
    expr_time_bytes = struct.pack("<2f", 0.0, 1.0)
    binary_chunk += expr_time_bytes
    expr_time_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": expr_time_byte_offset,
            "byteLength": len(expr_time_bytes),
        }
    )
    expr_time_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": expr_time_bv_index,
            "byteOffset": 0,
            "type": "SCALAR",
            "componentType": GL_FLOAT,
            "count": 2,
            "min": [0.0],
            "max": [1.0],
        }
    )
    # Weight output accessor: 0.0 → 1.0 (shared by morphtarget expression samplers)
    expr_weight_byte_offset = len(binary_chunk)
    expr_weight_bytes = struct.pack("<2f", 0.0, 1.0)
    binary_chunk += expr_weight_bytes
    expr_weight_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": expr_weight_byte_offset,
            "byteLength": len(expr_weight_bytes),
        }
    )
    expr_weight_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": expr_weight_bv_index,
            "byteOffset": 0,
            "type": "SCALAR",
            "componentType": GL_FLOAT,
            "count": 2,
            "min": [0.0],
            "max": [1.0],
        }
    )

    # Texture index output: texture_index → texture_index_2 (for STEP swap)
    tex_swap_byte_offset = len(binary_chunk)
    tex_swap_bytes = struct.pack("<2f", float(texture_index), float(texture_index_2))
    binary_chunk += tex_swap_bytes
    tex_swap_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": tex_swap_byte_offset,
            "byteLength": len(tex_swap_bytes),
        }
    )
    tex_swap_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": tex_swap_bv_index,
            "byteOffset": 0,
            "type": "SCALAR",
            "componentType": GL_FLOAT,
            "count": 2,
            "min": [float(texture_index)],
            "max": [float(texture_index_2)],
        }
    )

    # lookUp rotation output: identity → +20° around X (head looks up)
    look_up_angle = math.pi / 9  # 20 degrees
    look_up_rot_byte_offset = len(binary_chunk)
    look_up_rot_bytes = struct.pack(
        "<8f",
        0.0,
        0.0,
        0.0,
        1.0,  # identity quaternion [x,y,z,w] at t=0
        math.sin(look_up_angle / 2),
        0.0,
        0.0,
        math.cos(look_up_angle / 2),  # +20° around X [x,y,z,w] at t=1
    )
    binary_chunk += look_up_rot_bytes
    look_up_rot_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": look_up_rot_byte_offset,
            "byteLength": len(look_up_rot_bytes),
        }
    )
    look_up_rot_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": look_up_rot_bv_index,
            "byteOffset": 0,
            "type": "VEC4",
            "componentType": GL_FLOAT,
            "count": 2,
        }
    )

    # --- Build expression animations ---
    animation_dicts = json_dict.get("animations")
    if not isinstance(animation_dicts, list):
        animation_dicts = []
        json_dict["animations"] = animation_dicts

    # happy: morphtarget weight (LINEAR) + texture swap (STEP)
    happy_anim_index = len(animation_dicts)
    animation_dicts.append(
        make_json(
            {
                "name": "happy",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "path": "pointer",
                            "extensions": {
                                "KHR_animation_pointer": {
                                    "pointer": f"/nodes/{spine_index}/weights/0",
                                }
                            },
                        },
                    },
                    {
                        "sampler": 1,
                        "target": {
                            "path": "pointer",
                            "extensions": {
                                "KHR_animation_pointer": {
                                    "pointer": f"/materials/{material_index}"
                                    "/pbrMetallicRoughness/baseColorTexture/index",
                                }
                            },
                        },
                    },
                ],
                "samplers": [
                    {
                        "input": expr_time_acc_index,
                        "output": expr_weight_acc_index,
                        "interpolation": "LINEAR",
                    },
                    {
                        "input": expr_time_acc_index,
                        "output": tex_swap_acc_index,
                        "interpolation": "STEP",
                    },
                ],
            }
        )
    )

    # angry: morphtarget weight (LINEAR)
    angry_anim_index = len(animation_dicts)
    animation_dicts.append(
        make_json(
            {
                "name": "angry",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "path": "pointer",
                            "extensions": {
                                "KHR_animation_pointer": {
                                    "pointer": f"/nodes/{spine_index}/weights/1",
                                }
                            },
                        },
                    }
                ],
                "samplers": [
                    {
                        "input": expr_time_acc_index,
                        "output": expr_weight_acc_index,
                        "interpolation": "LINEAR",
                    }
                ],
            }
        )
    )

    # blink: morphtarget weight (STEP for binary toggle)
    blink_anim_index = len(animation_dicts)
    animation_dicts.append(
        make_json(
            {
                "name": "blink",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "path": "pointer",
                            "extensions": {
                                "KHR_animation_pointer": {
                                    "pointer": f"/nodes/{spine_index}/weights/2",
                                }
                            },
                        },
                    }
                ],
                "samplers": [
                    {
                        "input": expr_time_acc_index,
                        "output": expr_weight_acc_index,
                        "interpolation": "STEP",
                    }
                ],
            }
        )
    )

    # jawOpen: morphtarget weight (LINEAR)
    jaw_open_anim_index = len(animation_dicts)
    animation_dicts.append(
        make_json(
            {
                "name": "jawOpen",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "path": "pointer",
                            "extensions": {
                                "KHR_animation_pointer": {
                                    "pointer": f"/nodes/{spine_index}/weights/3",
                                }
                            },
                        },
                    }
                ],
                "samplers": [
                    {
                        "input": expr_time_acc_index,
                        "output": expr_weight_acc_index,
                        "interpolation": "LINEAR",
                    }
                ],
            }
        )
    )

    # lookUp: head joint rotation (LINEAR)
    look_up_anim_index = len(animation_dicts)
    animation_dicts.append(
        make_json(
            {
                "name": "lookUp",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "node": head_index,
                            "path": "rotation",
                        },
                    }
                ],
                "samplers": [
                    {
                        "input": expr_time_acc_index,
                        "output": look_up_rot_acc_index,
                        "interpolation": "LINEAR",
                    }
                ],
            }
        )
    )

    # Map expression name → animation index (used below for KHR_character_expression)
    expr_animation_indices = {
        "happy": happy_anim_index,
        "angry": angry_anim_index,
        "blink": blink_anim_index,
        "jawOpen": jaw_open_anim_index,
        "lookUp": look_up_anim_index,
    }

    # --- Reference pose animations (KHR_character_reference_pose) ---
    joint_node_indices = [
        hips_index,
        spine_index,
        head_index,
        left_upper_leg_index,
        left_lower_leg_index,
        left_foot_index,
        left_upper_arm_index,
        left_lower_arm_index,
        left_hand_index,
        right_upper_leg_index,
        right_lower_leg_index,
        right_foot_index,
        right_upper_arm_index,
        right_lower_arm_index,
        right_hand_index,
    ]
    joint_local_translations: list[tuple[float, float, float]] = [
        (0.0, 0.5, 0.0),  # hips
        (0.0, 0.25, 0.0),  # spine
        (0.0, 0.5, 0.0),  # head
        (0.125, 0.0, 0.0),  # leftUpperLeg
        (0.0, -0.25, 0.0),  # leftLowerLeg
        (0.0, -0.25, 0.0),  # leftFoot
        (0.25, 0.25, 0.0),  # leftUpperArm
        (0.25, 0.0, 0.0),  # leftLowerArm
        (0.25, 0.0, 0.0),  # leftHand
        (-0.125, 0.0, 0.0),  # rightUpperLeg
        (0.0, -0.25, 0.0),  # rightLowerLeg
        (0.0, -0.25, 0.0),  # rightFoot
        (-0.25, 0.25, 0.0),  # rightUpperArm
        (-0.25, 0.0, 0.0),  # rightLowerArm
        (-0.25, 0.0, 0.0),  # rightHand
    ]
    n_joints = len(joint_node_indices)

    # Single-keyframe time accessor at t=0 (shared by T-Pose and A-Pose)
    tpose_time_byte_offset = len(binary_chunk)
    tpose_time_bytes = struct.pack("<f", 0.0)
    binary_chunk += tpose_time_bytes
    tpose_time_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": tpose_time_byte_offset,
            "byteLength": len(tpose_time_bytes),
        }
    )
    tpose_time_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": tpose_time_bv_index,
            "byteOffset": 0,
            "type": "SCALAR",
            "componentType": GL_FLOAT,
            "count": 1,
            "min": [0.0],
            "max": [0.0],
        }
    )

    # T-Pose rotation: single identity quaternion shared by all joints
    tpose_rot_byte_offset = len(binary_chunk)
    tpose_rot_bytes = struct.pack("<4f", 0.0, 0.0, 0.0, 1.0)  # [x,y,z,w] identity
    binary_chunk += tpose_rot_bytes
    tpose_rot_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": tpose_rot_byte_offset,
            "byteLength": len(tpose_rot_bytes),
        }
    )
    tpose_rot_acc_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": tpose_rot_bv_index,
            "byteOffset": 0,
            "type": "VEC4",
            "componentType": 5126,  # GL_FLOAT
            "count": 1,
        }
    )

    # Joint translations packed sequentially; one accessor per joint via byteOffset
    tpose_trans_byte_offset = len(binary_chunk)
    flat_joint_translations: list[float] = []
    for jt in joint_local_translations:
        flat_joint_translations.extend(jt)
    tpose_trans_bytes = struct.pack(
        f"<{len(flat_joint_translations)}f", *flat_joint_translations
    )
    binary_chunk += tpose_trans_bytes
    tpose_trans_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": tpose_trans_byte_offset,
            "byteLength": len(tpose_trans_bytes),
        }
    )
    tpose_trans_acc_indices = list[int]()
    for ji in range(n_joints):
        trans_acc_index = len(accessor_dicts)
        tpose_trans_acc_indices.append(trans_acc_index)
        accessor_dicts.append(
            {
                "bufferView": tpose_trans_bv_index,
                "byteOffset": ji * 12,  # 3 floats * 4 bytes per VEC3
                "type": "VEC3",
                "componentType": GL_FLOAT,
                "count": 1,
            }
        )

    # T-Pose: identity rotations + local translations for all joints
    tpose_samplers: list[dict[str, object]] = [
        # Sampler 0: identity rotation shared by all joints
        {
            "input": tpose_time_acc_index,
            "output": tpose_rot_acc_index,
            "interpolation": "STEP",
        },
        *[
            {
                "input": tpose_time_acc_index,
                "output": tpose_trans_acc_indices[ji],
                "interpolation": "STEP",
            }
            for ji in range(n_joints)
        ],
    ]
    tpose_channels: list[dict[str, object]] = [
        *[
            {"sampler": 0, "target": {"node": node_index, "path": "rotation"}}
            for node_index in joint_node_indices
        ],
        *[
            {
                "sampler": ji + 1,
                "target": {"node": node_index, "path": "translation"},
            }
            for ji, node_index in enumerate(joint_node_indices)
        ],
    ]
    animation_dicts.append(
        make_json(
            {
                "name": "TPose",
                "channels": tpose_channels,
                "samplers": tpose_samplers,
                "extensions": {"KHR_character_reference_pose": {"poseType": "TPose"}},
            }
        )
    )

    # A-Pose: upper arms rotated ~45° downward, all other joints identity
    apose_arm_angle = math.pi / 4  # 45 degrees
    apose_rotations: list[tuple[float, float, float, float]] = []
    for node_index in joint_node_indices:
        if node_index == left_upper_arm_index:
            # Left arm: -45° around Z → arm goes from +X toward -Y
            a = -apose_arm_angle
            apose_rotations.append((0.0, 0.0, math.sin(a / 2), math.cos(a / 2)))
        elif node_index == right_upper_arm_index:
            # Right arm: +45° around Z → arm goes from -X toward -Y (symmetric)
            a = apose_arm_angle
            apose_rotations.append((0.0, 0.0, math.sin(a / 2), math.cos(a / 2)))
        else:
            apose_rotations.append((0.0, 0.0, 0.0, 1.0))  # identity

    apose_rot_byte_offset = len(binary_chunk)
    flat_apose_rots: list[float] = []
    for rot in apose_rotations:
        flat_apose_rots.extend(rot)
    apose_rot_bytes = struct.pack(f"<{len(flat_apose_rots)}f", *flat_apose_rots)
    binary_chunk += apose_rot_bytes
    apose_rot_bv_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": 0,
            "byteOffset": apose_rot_byte_offset,
            "byteLength": len(apose_rot_bytes),
        }
    )
    apose_rot_acc_indices = list[int]()
    for ji in range(n_joints):
        rot_acc_index = len(accessor_dicts)
        apose_rot_acc_indices.append(rot_acc_index)
        accessor_dicts.append(
            {
                "bufferView": apose_rot_bv_index,
                "byteOffset": ji * 16,  # 4 floats * 4 bytes per VEC4
                "type": "VEC4",
                "componentType": GL_FLOAT,
                "count": 1,
            }
        )

    # A-Pose: per-joint rotation samplers; reuse T-Pose translation accessors
    apose_samplers: list[dict[str, object]] = [
        *[
            {
                "input": tpose_time_acc_index,
                "output": apose_rot_acc_indices[ji],
                "interpolation": "STEP",
            }
            for ji in range(n_joints)
        ],
        *[
            {
                "input": tpose_time_acc_index,
                "output": tpose_trans_acc_indices[ji],
                "interpolation": "STEP",
            }
            for ji in range(n_joints)
        ],
    ]
    apose_channels: list[dict[str, object]] = [
        *[
            {"sampler": ji, "target": {"node": node_index, "path": "rotation"}}
            for ji, node_index in enumerate(joint_node_indices)
        ],
        *[
            {
                "sampler": n_joints + ji,
                "target": {"node": node_index, "path": "translation"},
            }
            for ji, node_index in enumerate(joint_node_indices)
        ],
    ]
    animation_dicts.append(
        make_json(
            {
                "name": "APose",
                "channels": apose_channels,
                "samplers": apose_samplers,
                "extensions": {"KHR_character_reference_pose": {"poseType": "APose"}},
            }
        )
    )

    extensions_used = json_dict.get("extensionsUsed")
    if not isinstance(extensions_used, list):
        extensions_used = []
        json_dict["extensionsUsed"] = extensions_used
    for extension_name in [
        "VRMC_vrm",
        "KHR_character",
        "KHR_xmp_json_ld",
        "KHR_character_skeleton_mapping",
        "KHR_character_expression",
        "KHR_character_expression_morphtarget",
        "KHR_character_expression_joint",
        "KHR_character_expression_texture",
        "KHR_character_expression_mapping",
        "KHR_character_reference_pose",
        "KHR_animation_pointer",
    ]:
        if extension_name not in extensions_used:
            extensions_used.append(extension_name)

    extensions_dict = json_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        extensions_dict = {}
        json_dict["extensions"] = extensions_dict

    khr_xmp_json_ld_dict = extensions_dict.get("KHR_xmp_json_ld")
    if not isinstance(khr_xmp_json_ld_dict, dict):
        khr_xmp_json_ld_dict = {}
        extensions_dict["KHR_xmp_json_ld"] = khr_xmp_json_ld_dict
    khr_xmp_json_ld_packets = khr_xmp_json_ld_dict.get("packets")
    if not isinstance(khr_xmp_json_ld_packets, list):
        khr_xmp_json_ld_packets = []
        khr_xmp_json_ld_dict["packets"] = khr_xmp_json_ld_packets
    packet_index = len(khr_xmp_json_ld_packets)
    khr_xmp_json_ld_packets.append(
        {
            "@context": {
                "dc": "http://purl.org/dc/elements/1.1/",
                "vrm": "https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/meta.md",
            },
            "dc:title": "Generated VRM 1.0 Debug Model",
            "dc:creator": {
                "@list": [
                    "Hiroshi Nosawa",
                ]
            },
            "dc:license": {
                "@list": [
                    "https://vrm.dev/licenses/1.0/",
                ]
            },
            "dc:created": "2026-02-07",
            "dc:rights": "Public Domain",
            "dc:publisher": "Hiroshi Nosawa Publishing",
            "dc:description": "Tomahawwwwwwwwwwwwk boooooomerang",
            "dc:subject": {"@list": ["90's Super Robot", "No Sweetness Allowed"]},
            "dc:source": "hiroshi-nosawa.example.com/debug",
            "khr:version": "1.0.0",
            "khr:thumbnailImage": image_index,
        }
    )

    asset_dict = json_dict.get("asset")
    if not isinstance(asset_dict, dict):
        asset_dict = {}
        json_dict["asset"] = asset_dict
    asset_extensions_dict = asset_dict.get("extensions")
    if not isinstance(asset_extensions_dict, dict):
        asset_extensions_dict = {}
        asset_dict["extensions"] = asset_extensions_dict
    asset_extensions_khr_xmp_json_ld_dict = asset_extensions_dict.get("KHR_xmp_json_ld")
    if not isinstance(asset_extensions_khr_xmp_json_ld_dict, dict):
        asset_extensions_khr_xmp_json_ld_dict = {}
        asset_extensions_dict["KHR_xmp_json_ld"] = asset_extensions_khr_xmp_json_ld_dict
    if not isinstance(asset_extensions_khr_xmp_json_ld_dict.get("packet"), int):
        asset_extensions_khr_xmp_json_ld_dict["packet"] = packet_index

    extensions_khr_character = {"rootNode": hips_index}
    extensions_dict["KHR_character"] = make_json(extensions_khr_character)

    # KHR_character_skeleton_mapping: maps standard rig vocabularies to model joints
    extensions_dict["KHR_character_skeleton_mapping"] = make_json(
        {
            "skeletalRigMappings": {
                "vrmHumanoid": {
                    "hips": "hips",
                    "spine": "spine",
                    "head": "head",
                    "leftUpperLeg": "leftUpperLeg",
                    "leftLowerLeg": "leftLowerLeg",
                    "leftFoot": "leftFoot",
                    "leftUpperArm": "leftUpperArm",
                    "leftLowerArm": "leftLowerArm",
                    "leftHand": "leftHand",
                    "rightUpperLeg": "rightUpperLeg",
                    "rightLowerLeg": "rightLowerLeg",
                    "rightFoot": "rightFoot",
                    "rightUpperArm": "rightUpperArm",
                    "rightLowerArm": "rightLowerArm",
                    "rightHand": "rightHand",
                },
                "unityHumanoid": {
                    "Hips": "hips",
                    "Spine": "spine",
                    "Head": "head",
                    "LeftUpperLeg": "leftUpperLeg",
                    "LeftLowerLeg": "leftLowerLeg",
                    "LeftFoot": "leftFoot",
                    "LeftUpperArm": "leftUpperArm",
                    "LeftLowerArm": "leftLowerArm",
                    "LeftHand": "leftHand",
                    "RightUpperLeg": "rightUpperLeg",
                    "RightLowerLeg": "rightLowerLeg",
                    "RightFoot": "rightFoot",
                    "RightUpperArm": "rightUpperArm",
                    "RightLowerArm": "rightLowerArm",
                    "RightHand": "rightHand",
                },
            }
        }
    )

    # KHR_character_expression: expression animations with typed sub-extensions
    extensions_dict["KHR_character_expression"] = make_json(
        {
            "expressions": [
                {
                    "expression": "happy",
                    "animation": expr_animation_indices["happy"],
                    "extensions": {
                        # morphtarget: channel 0 drives weight/0
                        "KHR_character_expression_morphtarget": {"channels": [0]},
                        # texture: channel 1 swaps texture
                        "KHR_character_expression_texture": {"channels": [1]},
                    },
                },
                {
                    "expression": "angry",
                    "animation": expr_animation_indices["angry"],
                    "extensions": {
                        "KHR_character_expression_morphtarget": {"channels": [0]},
                    },
                },
                {
                    "expression": "blink",
                    "animation": expr_animation_indices["blink"],
                    "extensions": {
                        "KHR_character_expression_morphtarget": {"channels": [0]},
                    },
                },
                {
                    "expression": "jawOpen",
                    "animation": expr_animation_indices["jawOpen"],
                    "extensions": {
                        "KHR_character_expression_morphtarget": {"channels": [0]},
                    },
                },
                {
                    "expression": "lookUp",
                    "animation": expr_animation_indices["lookUp"],
                    "extensions": {
                        # KHR_character_expression_joint: channel 0 drives head rotation
                        "KHR_character_expression_joint": {"channels": [0]},
                    },
                },
            ]
        }
    )

    # KHR_character_expression_mapping: maps expression vocabularies to source names
    extensions_dict["KHR_character_expression_mapping"] = make_json(
        {
            "expressionSetMappings": {
                "vrmPreset": {
                    "happy": [{"source": "happy", "weight": 1.0}],
                    "angry": [{"source": "angry", "weight": 1.0}],
                    "blink": [{"source": "blink", "weight": 1.0}],
                    "aa": [{"source": "jawOpen", "weight": 1.0}],
                    "lookUp": [{"source": "lookUp", "weight": 1.0}],
                },
                "arkit": {
                    "mouthSmileLeft": [{"source": "happy", "weight": 0.6}],
                    "mouthSmileRight": [{"source": "happy", "weight": 0.6}],
                    "browLowererLeft": [{"source": "angry", "weight": 0.4}],
                    "browLowererRight": [{"source": "angry", "weight": 0.4}],
                    "eyeBlinkLeft": [{"source": "blink", "weight": 0.8}],
                    "eyeBlinkRight": [{"source": "blink", "weight": 0.8}],
                    "jawOpen": [{"source": "jawOpen", "weight": 1.0}],
                    "eyeLookUpLeft": [{"source": "lookUp", "weight": 1.0}],
                    "eyeLookUpRight": [{"source": "lookUp", "weight": 1.0}],
                },
            }
        }
    )

    extensions_vrmc_vrm = {
        "specVersion": "1.0",
        "meta": {
            "licenseUrl": "https://vrm.dev/licenses/1.0/",
            "name": Path(argv[0]).name,
            "version": "UniVRMへのバグ報告用",
            "avatarPermission": "onlyAuthor",
            "allowExcessivelyViolentUsage": False,
            "allowExcessivelySexualUsage": False,
            "commercialUsage": "personalNonProfit",
            "allowPoliticalOrReligiousUsage": False,
            "allowAntisocialOrHateUsage": False,
            "creditNotation": "required",
            "allowRedistribution": False,
            "modification": "prohibited",
            "authors": [
                "https://github.com/saturday06",
                "https://github.com/KhronosGroup/glTF-Sample-Models/tree/b4c124c18171b6dead0350b6e46826e320a49a23/2.0",
            ],
            "otherLicenseUrl": "https://github.com/KhronosGroup/glTF-Sample-Models/tree/b4c124c18171b6dead0350b6e46826e320a49a23/2.0/",
            "thirdPartyLicenses": "こちらはUniVRMへのバグ報告を目的としたモデルのため"
            + "一般利用はお控えください",
        },
        "humanoid": {"humanBones": human_bones_dict},
        "firstPerson": {},
        "lookAt": {
            "offsetFromHeadBone": [0, 0, 0],
            "type": "bone",
            "rangeMapHorizontalInner": {"inputMaxValue": 0, "outputScale": 0},
            "rangeMapHorizontalOuter": {"inputMaxValue": 0, "outputScale": 0},
            "rangeMapVerticalDown": {"inputMaxValue": 0, "outputScale": 0},
            "rangeMapVerticalUp": {"inputMaxValue": 0, "outputScale": 0},
        },
        "expressions": {
            "preset": {
                "happy": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "angry": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "sad": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "relaxed": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "surprised": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "neutral": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "aa": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "ih": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "ou": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "ee": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "oh": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "blink": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "blinkLeft": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "blinkRight": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "lookUp": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "lookDown": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "lookLeft": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
                "lookRight": {
                    "isBinary": False,
                    "overrideBlink": "none",
                    "overrideLookAt": "none",
                    "overrideMouth": "none",
                },
            },
            "custom": {},
        },
    }
    extensions_dict["VRMC_vrm"] = make_json(extensions_vrmc_vrm)

    if not buffer_dicts:
        buffer0_dict = make_json({"byteLength": 0})
        buffer_dicts.append(buffer0_dict)
    buffer0_dict = buffer_dicts[0]
    if not isinstance(buffer0_dict, dict):
        raise TypeError

    buffer0_dict["byteLength"] = len(binary_chunk)

    for key in ["scenes", "nodes", "meshes", "buffers", "bufferViews", "accessors"]:
        root_dicts = json_dict.get(key)
        if isinstance(root_dicts, list) and not root_dicts:
            json_dict.pop(key)

    vrm1_bytes = pack_glb(json_dict, binary_chunk)
    output_path.write_bytes(vrm1_bytes)
    logger.info("Generated VRM1 model at: %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
