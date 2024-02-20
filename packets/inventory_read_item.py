from packets import NetworkPacket
from utils import BufferWriter

packet_id = 88


class Request(NetworkPacket):
    packet_id = packet_id

    def __init__(self, slot: int):
        self.slot = slot

    def serialize(self) -> bytes:
        writer = BufferWriter()

        writer.write_int8(self.slot)

        return bytes(writer)
