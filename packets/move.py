import logging

from packets import NetworkPacket
from packets.world_entities import update_entity, MovementState, EntityState
from utils import BufferWriter, BufferReader, StateType

packet_id = 4


class Packet(NetworkPacket):
    packet_id = packet_id

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def serialize(self):
        writer = BufferWriter()

        writer.write_float(self.x)
        writer.write_float(self.y)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()
        self.moves = []
        for _ in range(reader.read_int64()):
            self.moves.append((reader.read_float(), reader.read_float()))


def handle(packet: Response, client: "multiplayer.Client"):
    if packet.network_id not in client.game.entities:
        logging.error(f"Entity {packet.network_id} not found while trying to move")
        return

    entity = client.game.entities[packet.network_id]
    logging.debug(f"Moving entity {packet.network_id}")

    fake_entity_state = EntityState.__new__(EntityState)  # TODO: This is a hack, fix it
    fake_entity_state.state_id = 2
    fake_entity_state.state = MovementState(packet.moves, entity.is_moving,
                                            entity.states[StateType.MOVEMENT].state.speed)

    update_entity(packet.network_id, {StateType.MOVEMENT: fake_entity_state}, client)


receive_packet = Response
