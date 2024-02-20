import enum
import logging

from packets import NetworkPacket
from utils import BufferWriter, BufferReader

packet_id = 45  # Request is 44


class BarterStatus(enum.Enum):
    DECLINED = 0
    ACCEPTED = 1


class Request(NetworkPacket):
    packet_id = 44

    def __init__(self, status: "BarterStatus"):
        self.status: BarterStatus = status

    def serialize(self) -> bytes:
        writer = BufferWriter()

        writer.write_int8(self.status.value)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.status = BarterStatus(reader.read_int8())


def handle(packet: Response, client: "multiplayer.Client"):
    logging.info(f"Barter closed ({packet.status})")
    client.game.barter = None


receive_packet = Response
