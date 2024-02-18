import enum
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiplayer

from packets import NetworkPacket
from utils import BufferReader, StateType

packet_id = 91


class DamageType(enum.Enum):
    NONE = 0
    POISON = 1


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()
        self.damage = reader.read_int32()
        self.damage_type = DamageType(reader.read_int8())


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"{packet.network_id} took {packet.damage} damage of type {packet.damage_type}")
    entity = client.game.entities[packet.network_id]
    entity.states[StateType.HEALTH] -= packet.damage
