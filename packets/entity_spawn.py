import logging

from packets import NetworkPacket
from packets.world_entities import Entity, update_entity
from utils import BufferReader

packet_id = 8


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.data = Entity(reader)


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Spawning entity {packet.data.network_id}")
    if client.game.entities.get(packet.data.network_id):
        update_entity(packet.data.network_id, packet.data.states, client)
    else:
        client.game.entities[packet.data.network_id] = packet.data


receive_packet = Response
