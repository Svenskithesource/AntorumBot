import logging
from typing import TYPE_CHECKING

from packets import NetworkPacket
from utils import BufferReader, StateType

if TYPE_CHECKING:
    import multiplayer

packet_id = 56


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()


def handle(packet: Response, client: "multiplayer.Client"):
    logging.warning(
        f"Stopping combat with {client.game.entities[packet.network_id].states[StateType.INFO].state.name} ({packet.network_id})")


receive_packet = Response
