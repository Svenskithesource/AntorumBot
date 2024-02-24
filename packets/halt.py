from typing import TYPE_CHECKING

from packets import NetworkPacket
from utils import BufferReader

if TYPE_CHECKING:
    import multiplayer

packet_id = 13


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()


def handle(packet: Response, client: "multiplayer.Client"):
    client.game.entities[packet.network_id].stop_moving()
