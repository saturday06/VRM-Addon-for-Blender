"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


class GlbBinCollection:
    def __init__(self) -> None:
        self.vertex_attribute_bins: List[GlbBin] = []  # Glb_bin list
        self.image_bins: List[ImageBin] = []
        self.bin = bytearray()

    def pack_all(self) -> Tuple[Dict[str, Any], bytes]:
        bin_dict: Dict[str, Any] = {}
        byte_offset = 0
        bin_dict["bufferViews"] = []
        bin_dict["accessors"] = []

        for vab in self.vertex_attribute_bins:
            self.bin.extend(vab.bin)
            vab_dict = {
                "bufferView": self.get_new_buffer_view_id(),
                "byteOffset": 0,
                "type": vab.array_type,
                "componentType": vab.component_type,
                "count": vab.array_count,
                "normalized": False,
            }
            if vab.min_max:
                vab_dict["min"] = vab.min_max[0]
                vab_dict["max"] = vab.min_max[1]
            bin_dict["accessors"].append(vab_dict)
            bin_dict["bufferViews"].append(
                {
                    "buffer": 0,
                    "byteOffset": byte_offset,
                    "byteLength": vab.bin_length,
                }
            )
            byte_offset += vab.bin_length

        if len(self.image_bins) > 0:
            bin_dict["images"] = []
            for img in self.image_bins:
                self.bin.extend(img.bin)
                bin_dict["images"].append(
                    {
                        "name": img.name,
                        "bufferView": self.get_new_buffer_view_id(),
                        "mimeType": img.image_type,
                    }
                )
                bin_dict["bufferViews"].append(
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
