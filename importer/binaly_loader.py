"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import struct
from ..gl_const import GL_CONSTANS


class Binaly_Reader:
    def __init__(self, data: bytes)->None:
        self.data = data
        self.pos = 0

    def set_pos(self, pos):
        self.pos = pos

    def read_str(self, size):
        result = self.data[self.pos: self.pos + size]
        self.pos += size
        return result.decode("utf-8")

    def read_binaly(self, size):
        result = self.data[self.pos: self.pos + size]
        self.pos += size
        return result

    def read_uint(self):
        #unpackは内容の個数に関わらずタプルで返すので[0]が必要
        result = struct.unpack('<I',self.data[self.pos:self.pos + 4])[0]
        self.pos += 4
        return result

    def read_int(self):
        result = struct.unpack('<i', self.data[self.pos:self.pos + 4])[0]
        self.pos += 4
        return result

    def read_ushort(self):
        result = struct.unpack('<H', self.data[self.pos:self.pos + 2])[0]
        self.pos += 2
        return result

    def read_short(self):
        result = struct.unpack('<h', self.data[self.pos:self.pos + 2])[0]
        self.pos += 2
        return result

    def read_float(self):
        result = struct.unpack('<f', self.data[self.pos:self.pos + 4])[0]
        self.pos += 4
        return result

    def read_as_dataType(self,dataType:GL_CONSTANS):
        if dataType == GL_CONSTANS.UNSIGNED_INT:
            return self.read_uint()
        elif dataType == GL_CONSTANS.INT:
            return self.read_int()
        elif dataType == GL_CONSTANS.UNSIGNED_SHORT:
            return self.read_ushort()
        elif dataType == GL_CONSTANS.SHORT:
            return self.read_short()
        elif dataType == GL_CONSTANS.FLOAT:
            return self.read_float()
        else:
            print("unsuppoted type : {}".format(dataType))
            raise Exception
            


if "__main__" == __name__:
    Binaly_Reader(None)
