"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import struct
from typing import Union

from ..gl_constants import GlConstants


class BinaryReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def set_pos(self, pos: int) -> None:
        self.pos = pos

    def read_str(self, size: int) -> str:
        result = self.data[self.pos : self.pos + size]
        self.pos += size
        return result.decode("utf-8")

    def read_binary(self, size: int) -> bytes:
        result = self.data[self.pos : self.pos + size]
        self.pos += size
        return result

    def read_unsigned_int(self) -> int:
        # unpackは内容の個数に関わらずタプルで返すので[0]が必要
        result = struct.unpack("<I", self.data[self.pos : self.pos + 4])[0]
        if not isinstance(result, int):
            raise Exception()
        self.pos += 4
        return result

    def read_int(self) -> int:
        result = struct.unpack("<i", self.data[self.pos : self.pos + 4])[0]
        if not isinstance(result, int):
            raise Exception()
        self.pos += 4
        return result

    def read_unsigned_short(self) -> int:
        result = struct.unpack("<H", self.data[self.pos : self.pos + 2])[0]
        if not isinstance(result, int):
            raise Exception()
        self.pos += 2
        return result

    def read_short(self) -> int:
        result = struct.unpack("<h", self.data[self.pos : self.pos + 2])[0]
        if not isinstance(result, int):
            raise Exception()
        self.pos += 2
        return result

    def read_float(self) -> float:
        result = struct.unpack("<f", self.data[self.pos : self.pos + 4])[0]
        if not isinstance(result, float):
            raise Exception()
        self.pos += 4
        return result

    def read_unsigned_byte(self) -> int:
        result = struct.unpack("<B", self.data[self.pos : self.pos + 1])[0]
        if not isinstance(result, int):
            raise Exception()
        self.pos += 1
        return result

    def read_as_data_type(self, data_type: int) -> Union[int, float]:
        if data_type == GlConstants.UNSIGNED_INT:
            return self.read_unsigned_int()
        if data_type == GlConstants.INT:
            return self.read_int()
        if data_type == GlConstants.UNSIGNED_SHORT:
            return self.read_unsigned_short()
        if data_type == GlConstants.SHORT:
            return self.read_short()
        if data_type == GlConstants.FLOAT:
            return self.read_float()
        if data_type == GlConstants.UNSIGNED_BYTE:
            return self.read_unsigned_byte()
        print("unsupported type : {}".format(data_type))
        raise Exception


if __name__ == "__main__":
    BinaryReader(b"Hello")
