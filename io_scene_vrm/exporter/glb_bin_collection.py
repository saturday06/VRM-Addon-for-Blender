"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from ..common.deep import Json, make_json


class GlbBinCollection:
    def __init__(self) -> None:
        self.vertex_attribute_bins: List[GlbBin] = []  # Glb_bin list
        self.image_bins: List[ImageBin] = []
        self.bin = bytearray()

    def pack_all(self) -> Tuple[Dict[str, Json], bytes]:
        bin_dict: Dict[str, Json] = {}
        byte_offset = 0
        buffer_view_dicts: List[Json] = []
        bin_dict["bufferViews"] = buffer_view_dicts
        accessor_dicts: List[Json] = []
        bin_dict["accessors"] = accessor_dicts

        for vab in self.vertex_attribute_bins:
            self.bin.extend(vab.bin)
            vab_dict: Dict[str, Json] = {
                "bufferView": self.get_new_buffer_view_id(),
                "byteOffset": 0,
                "type": vab.array_type,
                "componentType": vab.component_type,
                "count": vab.array_count,
                "normalized": False,
            }
            if vab.min_max:
                vab_dict["min"] = make_json(vab.min_max[0])
                vab_dict["max"] = make_json(vab.min_max[1])
            accessor_dicts.append(vab_dict)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": byte_offset,
                    "byteLength": vab.bin_length,
                }
            )
            byte_offset += vab.bin_length

        if self.image_bins:
            image_dicts: List[Json] = []
            bin_dict["images"] = image_dicts
            for img in self.image_bins:
                self.bin.extend(img.bin)
                image_dicts.append(
                    {
                        "name": img.name,
                        "bufferView": self.get_new_buffer_view_id(),
                        "mimeType": img.image_type,
                    }
                )
                buffer_view_dicts.append(
                    {
                        "buffer": 0,
                        "byteOffset": byte_offset,
                        "byteLength": img.bin_length,
                    }
                )
                byte_offset += img.bin_length

        bin_dict["buffers"] = [{"byteLength": byte_offset}]

        buffer_view_and_accessors_ordered_dict = bin_dict
        return buffer_view_and_accessors_ordered_dict, bytes(self.bin)

    buffer_count = 0

    def get_new_buffer_view_id(self) -> int:
        self.buffer_count += 1
        return self.buffer_count - 1

    def get_new_image_id(self) -> int:
        return len(self.image_bins)

    def get_new_glb_bin_id(self) -> int:
        return len(self.vertex_attribute_bins)


@dataclass
class BaseBin:
    bin: bytes
    glb_bin_collection: GlbBinCollection
    bin_length: int = field(init=False)

    def __post_init__(self) -> None:
        self.bin_length = len(self.bin)


class ImageBin(BaseBin):
    def __init__(
        self,
        image_bin: bytes,
        name: str,
        image_type: str,
        glb_bin_collection: GlbBinCollection,
    ) -> None:
        super().__init__(image_bin, glb_bin_collection)
        self.name = name
        self.image_type = image_type
        self.image_id = glb_bin_collection.get_new_image_id()
        glb_bin_collection.image_bins.append(self)


class GlbBin(BaseBin):
    def __init__(
        self,
        binary: Union[bytes, bytearray],
        array_type: str,
        component_type: int,
        array_count: int,
        min_max_tuple: Optional[List[List[float]]],
        glb_bin_collection: GlbBinCollection,
    ) -> None:
        if isinstance(binary, bytearray):
            binary = bytes(binary)
        super().__init__(binary, glb_bin_collection)
        self.array_type = array_type  # String: scalar, VEC3 etc...
        self.component_type = component_type  # GL_CONSTANTS:FLOAT, uint etc...
        self.array_count = array_count  # array num
        self.min_max = min_max_tuple  # position attribute must need min_max
        self.accessor_id = glb_bin_collection.get_new_glb_bin_id()
        glb_bin_collection.vertex_attribute_bins.append(self)
