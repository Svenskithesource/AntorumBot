import asyncio
import base64
import datetime
import enum
import logging
from typing import Literal, List, TYPE_CHECKING, Dict, Tuple, Union
import struct

if TYPE_CHECKING:
    import multiplayer
    from packets.inventory import InventoryItem
    from packets.inventory_add import ItemResource
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
        else game.entities[network_id].position


def get_player_id_from_username(username: str, game: "multiplayer.Game"):
    for entity in game.entities.values():
        if entity.name == username:
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


def is_nearby(coords: Tuple[float, float], other_coords: Tuple[float, float], distance: float = 5):
    return abs(coords[0] - other_coords[0]) <= distance and abs(coords[1] - other_coords[1]) <= distance


def distance_to_entity(coords: Tuple[float, float], entity: "Entity"):
    return ((coords[0] - entity.position[0]) ** 2 +
            (coords[1] - entity.position[1]) ** 2) ** 0.5


def get_nearest_entity(coords: Tuple[float, float], entities: Dict[int, "Entity"]) -> Union[None, "Entity"]:
    nearest_entity = None
    nearest_distance = float("inf")

    for entity in entities.values():
        if entity.position:
            distance = ((coords[0] - entity.position[0]) ** 2 +
                        (coords[1] - entity.position[1]) ** 2)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_entity = entity

    return nearest_entity


def distance_to_closest_enemy(coords: Tuple[float, float], entities: Dict[int, "Entity"]):
    nearest_distance = float("inf")

    for entity in entities.values():
        if entity.position and entity.name in ENEMIES:
            distance = entity.distance_to(coords)

            if distance < nearest_distance:
                nearest_distance = distance

    return nearest_distance


def get_nearest_safe_entity(coords: Tuple[float, float], requested_entities: Dict[int, "Entity"],
                            all_entities: Dict[int, "Entity"], safe_distance: float = 10):
    nearest_entity = None
    nearest_distance = float("inf")

    for entity in requested_entities.values():
        if entity.position != (-1, -1) and distance_to_closest_enemy(
                entity.position, all_entities) > safe_distance:
            distance = entity.distance_to(coords)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_entity = entity

    return nearest_entity


def time_to_dest(start_coords: Tuple[float, float], dest_coords: Tuple[float, float], speed: float):
    return ((dest_coords[0] - start_coords[0]) ** 2 + (dest_coords[1] - start_coords[1]) ** 2) ** 0.5 / speed


def time_to_dests(start_coords: Tuple[float, float], destinations: List[Tuple[float, float]], speed: float):
    if not destinations:
        return 0

    time = 0
    for i in range(len(destinations) - 1):
        time += time_to_dest(destinations[i], destinations[i + 1], speed)

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


def inventory_contains_resource_id(resource_id: int, inventory: Dict[int, "InventoryItem"], amount: int):
    total = 0

    for item in inventory.values():
        if item.resource.resource_id == resource_id:
            total += item.amount

    return total >= amount


async def wait_for(predicate, timeout: int):
    i = 0

    while not predicate():
        await asyncio.sleep(0.1)

        i += 1
        if i > timeout * 10:
            return False

    return True


def get_resource_by_name(name: str, resources: Dict[int, "ItemResource"]):
    for resource in resources.values():
        if resource.resource_name == name.lower():
            return resource
    return None


def get_inventory_slot_by_resource_id(resource_id: int, inventory: Dict[int, "InventoryItem"]):
    for slot, item in inventory.items():
        if item.resource.resource_id == resource_id:
            return slot

    return None


def amount_of_resource_in_inventory(resource_id: int, inventory: Dict[int, "InventoryItem"]):
    total = 0

    for slot, item in inventory.items():
        if item.resource.resource_id == resource_id:
            total += item.amount

    return total


def has_sufficient_level(levels: Dict[int, List[str]], level: int, item: str):
    for l in levels.keys():
        if l <= level:
            if item in levels[l]:
                return True
        else:
            return False


async def emulate_move(start_coords: Tuple[float, float], destinations: List[Tuple[float, float]], speed: float,
                       client: "multiplayer.Client"):
    time_to_next = time_to_dest(start_coords, destinations[0], speed)
    begin_coords = start_coords
    end_coords = destinations[0]

    for i in range(len(destinations)):
        time_left = time_to_next
        while time_left > 0:
            await asyncio.sleep(1)

            if not client.game.entities[client.game.local_player.network_id].is_moving:
                return

            time_left -= 1

            client.game.local_player.position = (
                start_coords[0] + (end_coords[0] - begin_coords[0]) * (1 - time_left / time_to_next),
                begin_coords[1] + (end_coords[1] - begin_coords[1]) * (1 - time_left / time_to_next)
            )

            logging.debug(f"Emulated move to {client.game.local_player.position}")

        if i + 1 >= len(destinations) - 1:
            break

        time_to_next = time_to_dest(destinations[i], destinations[i + 1], speed)
        start_coords = destinations[i]
        end_coords = destinations[i + 1]

    client.game.local_player.position = destinations[-1]
    client.game.entities[client.game.local_player.network_id].stop_moving()
