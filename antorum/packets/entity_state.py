import logging

from antorum.packets import NetworkPacket
from antorum.packets.world_entities import EntityState, update_entity
from antorum.utils import BufferReader

packet_id = 27


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()
        self.state = EntityState(reader)


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received entity state {packet.state.state_id} for entity {packet.network_id}")
    update_entity(packet.network_id, {packet.state.state_id: packet.state}, client)


receive_packet = Response
