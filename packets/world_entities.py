import enum
import json
import logging
from dataclasses import dataclass
from typing import Tuple, List, Dict

from game import Game
from packets import NetworkPacket
from packets.inventory import ItemSlot, InventoryItem, ItemPropertyBag
from packets.inventory import Response as InventoryResponse
from player import Player
from utils import BufferReader, get_entity_from_player_id

packet_id = 29


class InteractionType(enum.Enum):
    ATTACK = 0
    COOK_ON = 1
    TALK_TO = 2
    WALK_TO = 3
    EXAMINE = 4
    PICK_UP = 5
    BARTER = 6
    FORAGE = 7
    FISH = 8
    ACCESS_VAULT = 9
    CRAFT = 10
    PERFORM_RITUAL = 11
    MINE = 12
    SMELT_AT = 13
    OPEN = 14


@dataclass
class InfoState:
    name: str
    model_id: int


@dataclass
class TransformState:
    position: Tuple[float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]


@dataclass
class MovementState:
    destinations: List[Tuple[float, float]]
    is_moving: bool
    speed: float


@dataclass
class HealthState:
    health: int
    max_health: int


@dataclass
class ItemState:
    amount: int
    network_id: int


@dataclass
class InteractableState:
    interactions: List[InteractionType]


@dataclass
class PlayerState:
    player_id: int


@dataclass
class EquipmentState:
    hair: int
    facial_hair: int
    hair_color: int
    facial_hair_color: int
    skin_color: int
    shirt_color: int
    pants_color: int
    equipped: Dict[ItemSlot, InventoryItem]
    bulk: int
    height: int


@dataclass
class NPCState:
    pass


@dataclass
class FisherState:
    is_fishing: bool
    fish_node_network_id: int
    bobber_position: Tuple[float, float]


@dataclass
class ClassState:
    title: str
    artisan: int
    explorer: int
    warrior: int
    ascetic: int


@dataclass
class QuestGiverState:
    quest_id: int


@dataclass
class MinerState:
    in_progress: bool
    node_network_id: int


@dataclass
class AnimatorState:
    pass  # TODO: Implement


class EntityState:
    def __init__(self, reader: BufferReader):
        self.state_id = reader.read_int32()

        if self.state_id == 0:
            self.state = InfoState(reader.read_string(), reader.read_int16())
        elif self.state_id == 1:
            self.state = TransformState((reader.read_float(), reader.read_float()),
                                        (reader.read_float(), reader.read_float(), reader.read_float()),
                                        (reader.read_float(), reader.read_float(), reader.read_float()))
        elif self.state_id == 2:
            self.state = MovementState([(reader.read_float(), reader.read_float()) for _ in range(reader.read_int64())],
                                       reader.read_bool(), reader.read_float())
        elif self.state_id == 3:
            self.state = HealthState(reader.read_int32(), reader.read_int32())
        elif self.state_id == 4:
            self.state = ItemState(reader.read_int32(), reader.read_int64())
        elif self.state_id == 5:
            self.state = InteractableState([InteractionType(reader.read_int8()) for _ in range(reader.read_int64())])
        elif self.state_id == 6:
            self.state = PlayerState(reader.read_int64())
        elif self.state_id == 7:
            hair = reader.read_int8()
            facial_hair = reader.read_int8()
            hair_color = reader.read_int8()
            facial_hair_color = reader.read_int8()
            skin_color = reader.read_int8()
            shirt_color = reader.read_int8()
            pants_color = reader.read_int8()
            bulk = reader.read_int8()
            height = reader.read_int8()

            equipped = InventoryResponse().parse(reader)

            self.state = EquipmentState(hair, facial_hair, hair_color, facial_hair_color, skin_color, shirt_color,
                                        pants_color, equipped, bulk, height)
        elif self.state_id == 8:
            self.state = NPCState()
        elif self.state_id == 9:
            self.state = FisherState(reader.read_bool(), reader.read_int64(),
                                     (reader.read_float(), reader.read_float()))
        elif self.state_id == 10:
            self.state = ClassState(reader.read_string(), reader.read_int8(), reader.read_int8(), reader.read_int8(),
                                    reader.read_int8())
        elif self.state_id == 11:
            self.state = QuestGiverState(reader.read_int64())
        elif self.state_id == 12:
            self.state = MinerState(reader.read_bool(), reader.read_int64())
        elif self.state_id == 13:
            # TODO: Implement, not necessary for now
            reader.read_int64()
            for _ in range(reader.read_int64()):
                reader.read_string(), reader.read_bool()
            self.state = AnimatorState()
        else:
            logging.error(f"Unknown state id {self.state_id}")
            self.state = None

    def __repr__(self):
        return f"EntityState({self.state_id}, {self.state})"


class Entity:
    def __init__(self, reader: BufferReader):
        self.network_id = reader.read_int64()

        self.states = {}

        amount = reader.read_int64()
        for i in range(amount):
            state = EntityState(reader)
            self.states[state.state_id] = state

    def __repr__(self):
        return f"Entity({self.network_id}, {self.states})"


class Response(NetworkPacket):
    packet_id = packet_id

    def read_entities(self, reader: BufferReader):
        entities = []
        count = reader.read_int64()
        for _ in range(count):
            entities.append(Entity(reader))
        return entities

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.coords = reader.read_int32(), reader.read_int32()
        self.entities: List[Entity] = self.read_entities(reader)
        self.removed_entities = [reader.read_int64() for _ in range(reader.read_int64())]
        self.full_sync = reader.read_bool()


def update_player(states: Dict[int, EntityState], client: "multiplayer.Client"):
    for state in states.values():
        if state.state_id == 0:
            client.game.local_player.username = state.state.name
        if state.state_id == 1:
            client.game.local_player.position = state.state.position
        elif state.state_id == 3:
            client.game.local_player.health = state.state.health
            client.game.local_player.max_health = state.state.max_health


def update_entity(network_id: int, states: Dict[int, EntityState], client: "multiplayer.Client"):
    if client.game.entities.get(network_id):
        for state in states.values():
            client.game.entities[network_id].states[state.state_id] = state

    if network_id == client.game.local_player.network_id:
        update_player(states, client)


def update_entities(entities: List[Entity], is_full_sync: bool, removed_entities: List[int],
                    client: "multiplayer.Client"):
    for network_id in removed_entities:
        client.game.entities.pop(network_id, None)

    if is_full_sync:
        client.game.entities.clear()
        client.game.entities = {entity.network_id: entity for entity in entities}

        player_entity = client.game.entities[client.game.local_player.network_id]
        update_player(player_entity.states, client)
    else:
        for entity in entities:
            if not client.game.entities.get(entity.network_id):
                client.game.entities[entity.network_id] = entity
            else:
                update_entity(entity.network_id, entity.states, client)


def handle(packet: Response, client: "multiplayer.Client"):
    if not client.game:
        player_entity = get_entity_from_player_id(client.player_id, packet.entities)
        network_id = player_entity.network_id

        client.game = Game(client.player_id, network_id, client)

    logging.debug(f"Received {len(packet.entities)} entities, at coords {packet.coords}")
    logging.debug(f"Removed {len(packet.removed_entities)} entities")
    logging.debug(f"Full sync: {packet.full_sync}")
    for entity in packet.entities:
        logging.debug(f"Entity {entity.network_id} with {len(entity.states)} states")
        for state in entity.states.values():
            logging.debug(f"State: {state.state}")

    update_entities(packet.entities, packet.full_sync, packet.removed_entities, client)

    logging.debug(f"Player updated: {client.game.local_player}")


receive_packet = Response
