from typing import TYPE_CHECKING

from antorum.packets import NetworkPacket
from antorum.utils import BufferReader

if TYPE_CHECKING:
    from antorum import multiplayer

packet_id = 13


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()


def handle(packet: Response, client: "multiplayer.Client"):
    client.game.entities[packet.network_id].stop_moving()
