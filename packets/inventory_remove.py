from utils import BufferReader
from packets import NetworkPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiplayer

packet_id = 21


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)

        self.index = reader.read_int8()
        self.amount = reader.read_int32()


def handle(packet: Response, client: "multiplayer.Client"):
    client.game.local_player.inventory[packet.index].amount -= packet.amount

    if client.game.local_player.inventory[packet.index].amount <= 0:
        client.game.local_player.inventory.pop(packet.index)


receive_packet = Response
