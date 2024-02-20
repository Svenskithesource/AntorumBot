import base64
import datetime
import enum
from typing import Literal, List, TYPE_CHECKING, Dict, Tuple
import struct

if TYPE_CHECKING:
    import multiplayer
    from packets.inventory import InventoryItem
    from packets.world_entities import Entity
    from packets.chat import ChatMessage

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5

BYTEORDER: Literal['little', 'big'] = "big"

ENEMIES = ["Gremneer"]


class StateType(enum.Enum):
    INFO = 0
    TRANSFORM = 1
    MOVEMENT = 2
    HEALTH = 3
    ITEM = 4
    INTERACTABLE = 5
    PLAYER = 6
    EQUIPMENT = 7
    NPC = 8
    FISHER = 9
    CLASS = 10
    QUEST_GIVER = 11
    MINER = 12
    ANIMATOR = 13


class EncryptionHelper:
    def __init__(self, key):
        self.key = RSA.import_key(key)

    def encrypt(self, data):
        return base64.b64encode(PKCS1_v1_5.new(self.key.public_key()).encrypt(data))


class BufferReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pointer = 0

    def read(self, size: int) -> bytes:
        data = self.data[self.pointer:self.pointer + size]
        self.pointer += size
        return data

    def read_bool(self) -> bool:
        return bool(self.read_int8())

    def read_int8(self, signed: bool = False) -> int:
        return int.from_bytes(self.read(1), BYTEORDER, signed=signed)

    def read_int16(self, signed: bool = False) -> int:
        return int.from_bytes(self.read(2), BYTEORDER, signed=signed)

    def read_int32(self, signed: bool = False) -> int:
        return int.from_bytes(self.read(4), BYTEORDER, signed=signed)

    def read_int64(self, signed: bool = False) -> int:
        return int.from_bytes(self.read(8), BYTEORDER, signed=signed)

    def read_string(self) -> str:
        length = self.read_int64()
        return self.read(length).decode("utf-8")

    def read_float(self) -> float:
        return struct.unpack((">" if BYTEORDER == "big" else "<") + "f", self.read(4))[0]


class BufferWriter:
    def __init__(self):
        self.data = b""

    def __bytes__(self):
        return self.data

    def write(self, data: bytes):
        self.data += data

    def write_int8(self, value: int):
        self.write(value.to_bytes(1, BYTEORDER))

    def write_int16(self, value: int):
        self.write(value.to_bytes(2, BYTEORDER))

    def write_int32(self, value: int):
        self.write(value.to_bytes(4, BYTEORDER))

    def write_int64(self, value: int):
        self.write(value.to_bytes(8, BYTEORDER))

    def write_float(self, value: float):
        self.write(struct.pack((">" if BYTEORDER == "big" else "<") + "f", value))

    def write_string(self, value: str):
        self.write_int64(len(value))
        self.write(value.encode("utf-8"))

    def write_bytes(self, value: bytes):
        self.write_int64(len(value))
        self.write(value)


def get_entity_from_player_id(player_id: int, entities: List["world_entities.Entity"]):
    for entity in entities:
        if entity.states.get(StateType.PLAYER) and entity.states[StateType.PLAYER].state.player_id == player_id:
            return entity
    return None


def get_future_position_from_entity(network_id, game: "multiplayer.Game"):
    return game.entities[network_id].states[StateType.MOVEMENT].state.destinations[-1] \
        if game.entities[network_id].states[StateType.MOVEMENT].state.destinations \
        else game.entities[network_id].states[StateType.TRANSFORM].state.position


def get_player_id_from_username(username: str, game: "multiplayer.Game"):
    for entity in game.entities.values():
        if entity.states.get(StateType.INFO) and entity.states[StateType.INFO].state.name == username:
            return entity.states[StateType.PLAYER].state.player_id
    return None


def get_inventory_diff(old_inventory: Dict[int, "InventoryItem"], new_inventory: Dict[int, "InventoryItem"]):
    added = {}
    removed = {}

    for index, item in new_inventory.items():
        if index not in old_inventory:
            added[index] = item
        elif item.resource.resource_id != old_inventory[index].resource.resource_id:
            removed[index] = old_inventory[index]
            added[index] = item
        elif item.amount != old_inventory[index].amount:
            added[index] = item

    for index, item in old_inventory.items():
        if index not in new_inventory:
            removed[index] = item

    return added, removed


def map_to_game_coords(coords: List[Tuple[float, float]]):
    return [((x / 16) * 3, ((5632 - y) / 16) * 3) for x, y in coords]


def is_nearby(coords: Tuple[float, float], other_coords: Tuple[float, float], distance: float):
    return abs(coords[0] - other_coords[0]) <= distance and abs(coords[1] - other_coords[1]) <= distance


def distance_to_entity(coords: Tuple[float, float], entity: "Entity"):
    return ((coords[0] - entity.states[StateType.TRANSFORM].state.position[0]) ** 2 +
            (coords[1] - entity.states[StateType.TRANSFORM].state.position[1]) ** 2) ** 0.5


def get_nearest_entity(coords: Tuple[float, float], entities: Dict[int, "Entity"]):
    nearest_entity = None
    nearest_distance = float("inf")

    for entity in entities.values():
        if entity.states.get(StateType.TRANSFORM):
            distance = ((coords[0] - entity.states[StateType.TRANSFORM].state.position[0]) ** 2 +
                        (coords[1] - entity.states[StateType.TRANSFORM].state.position[1]) ** 2)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_entity = entity

    return nearest_entity


def distance_to_closest_enemy(coords: Tuple[float, float], entities: Dict[int, "Entity"]):
    nearest_distance = float("inf")

    for entity in entities.values():
        if entity.states.get(StateType.TRANSFORM) and entity.states.get(StateType.INFO) and entity.states.get(
                StateType.INFO).state.name in ENEMIES:
            distance = distance_to_entity(coords, entity)

            if distance < nearest_distance:
                nearest_distance = distance

    return nearest_distance


def get_nearest_safe_entity(coords: Tuple[float, float], requested_entities: Dict[int, "Entity"],
                            all_entities: Dict[int, "Entity"], safe_distance: float = 10):
    nearest_entity = None
    nearest_distance = float("inf")

    for entity in requested_entities.values():
        if entity.states.get(StateType.TRANSFORM) and distance_to_closest_enemy(
                entity.states[StateType.TRANSFORM].state.position, all_entities) > safe_distance:
            distance = distance_to_entity(coords, entity)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_entity = entity

    return nearest_entity


def time_to_dest(start_coords: Tuple[float, float], destinations: List[Tuple[float, float]], speed: float):
    if not destinations:
        return 0

    time = 0
    for i in range(len(destinations) - 1):
        time += ((destinations[i][0] - destinations[i + 1][0]) ** 2 +
                 (destinations[i][1] - destinations[i + 1][1]) ** 2) ** 0.5 / speed

    time += ((destinations[0][0] - start_coords[0]) ** 2 + (destinations[0][1] - start_coords[1]) ** 2) ** 0.5 / speed
    return time


def coords_in_bounds(coords: Tuple[float, float], bounds: Tuple[Tuple[float, float], Tuple[float, float]]):
    return bounds[0][0] <= coords[0] <= bounds[1][0] and bounds[0][1] <= coords[1] <= bounds[1][1]


def message_contains_since(message: str, messages: List[Tuple[datetime.datetime, "ChatMessage"]],
                           since: datetime.datetime):
    for timestamp, chat_message in reversed(messages):
        if timestamp < since:
            return False
        if message in chat_message.message:
            return True

    return False
