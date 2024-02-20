from packets import NetworkPacket
from utils import BufferWriter

packet_id = 24


class Request(NetworkPacket):
    packet_id = packet_id

    def __init__(self, index: int, amount: int):
        self.index = index
        self.amount = amount

    def serialize(self) -> bytes:
        writer = BufferWriter()

        writer.write_int8(self.index)
        writer.write_int32(self.amount)

        return bytes(writer)
