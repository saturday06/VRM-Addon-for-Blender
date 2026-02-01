#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import logging
import struct
import sys
from pathlib import Path

from io_scene_vrm.common.deep import Json, make_json
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
            "componentType": 5126,  # GL_FLOAT
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
            "componentType": 5126,  # GL_FLOAT
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
                "componentType": 5126,  # GL_FLOAT
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

    extensions_used = json_dict.get("extensionsUsed")
    if not isinstance(extensions_used, list):
        extensions_used = []
        json_dict["extensionsUsed"] = extensions_used
    if "VRMC_vrm" not in extensions_used:
        extensions_used.append("VRMC_vrm")

    extensions_dict = json_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        extensions_dict = {}
        json_dict["extensions"] = extensions_dict

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
