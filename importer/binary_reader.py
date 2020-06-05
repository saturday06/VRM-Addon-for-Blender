"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import struct
from ..gl_constants import GlConstants


class BinaryReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def set_pos(self, pos):
        self.pos = pos

    def read_str(self, size):
        result = self.data[self.pos: self.pos + size]
        self.pos += size
        return result.decode("utf-8")

    def read_binary(self, size):
        result = self.data[self.pos: self.pos + size]
        self.pos += size
        return result

    def read_unsigned_int(self):
        # unpackは内容の個数に関わらずタプルで返すので[0]が必要
        result = struct.unpack("<I", self.data[self.pos: self.pos + 4])[0]
        self.pos += 4
        return result

    def read_int(self):
        result = struct.unpack("<i", self.data[self.pos: self.pos + 4])[0]
        self.pos += 4
        return result

    def read_unsigned_short(self):
        result = struct.unpack("<H", self.data[self.pos: self.pos + 2])[0]
        self.pos += 2
        return result

    def read_short(self):
        result = struct.unpack("<h", self.data[self.pos: self.pos + 2])[0]
        self.pos += 2
        return result

    def read_float(self):
        result = struct.unpack("<f", self.data[self.pos: self.pos + 4])[0]
        self.pos += 4
        return result

    def read_unsigned_byte(self):
        result = struct.unpack("<B", self.data[self.pos: self.pos + 1])[0]
        self.pos += 1
        return result

    def read_as_data_type(self, data_type: GlConstants):
        if data_type == GlConstants.UNSIGNED_INT:
            return self.read_unsigned_int()
        elif data_type == GlConstants.INT:
            return self.read_int()
        elif data_type == GlConstants.UNSIGNED_SHORT:
            return self.read_unsigned_short()
        elif data_type == GlConstants.SHORT:
            return self.read_short()
        elif data_type == GlConstants.FLOAT:
            return self.read_float()
        elif data_type == GlConstants.UNSIGNED_BYTE:
            return self.read_unsigned_byte()
        else:
            print("unsupported type : {}".format(data_type))
            raise Exception


if "__main__" == __name__:
    BinaryReader(b"Hello")
