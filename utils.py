from typing import Literal

import rsa

BYTEORDER: Literal['little', 'big'] = "big"


class EncryptionHelper:
    def __init__(self, key):
        self.key = key

    def encrypt(self, data):
        return rsa.encrypt(data, self.key)


class BufferReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pointer = 0

    def read(self, size: int):
        data = self.data[self.pointer:self.pointer + size]
        self.pointer += size
        return data

    def read_int8(self, signed: bool = False):
        return int.from_bytes(self.read(1), BYTEORDER, signed=signed)

    def read_int16(self, signed: bool = False):
        return int.from_bytes(self.read(2), BYTEORDER, signed=signed)

    def read_int32(self, signed: bool = False):
        return int.from_bytes(self.read(4), BYTEORDER, signed=signed)

    def read_int64(self, signed: bool = False):
        return int.from_bytes(self.read(8), BYTEORDER, signed=signed)

    def read_string(self):
        length = self.read_int64()
        return self.read(length).decode("utf-8")
