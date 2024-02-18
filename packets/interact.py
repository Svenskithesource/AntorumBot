from typing import TYPE_CHECKING

from packets import NetworkPacket
from packets.world_entities import InteractionType
from utils import BufferWriter, BufferReader, StateType

if TYPE_CHECKING:
    import multiplayer

packet_id = 11


class Packet(NetworkPacket):
    packet_id = packet_id

    def __init__(self, network_id: int, interaction_type: InteractionType):
        self.network_id = network_id
        self.interaction_type = interaction_type

    def serialize(self):
        writer = BufferWriter()

        writer.write_int64(self.network_id)
        writer.write_int8(self.interaction_type.value)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)

        self.src_network_id = reader.read_int64()
        self.target_network_id = reader.read_int64()
        self.damage = reader.read_int32()
        self.damage_blocked = reader.read_int32()
        self.did_dodge = reader.read_int8() == 1
        self.did_miss = reader.read_int8() == 1


def handle(packet: Response, client: "multiplayer.Client"):
    if not packet.did_dodge and not packet.did_miss:
        client.game.entities[packet.target_network_id].states[
            StateType.HEALTH].state.health -= packet.damage - packet.damage_blocked


receive_packet = Response
