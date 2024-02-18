import base64
import enum
from typing import Literal, List, TYPE_CHECKING, Dict
import struct

if TYPE_CHECKING:
    import multiplayer
    from packets.inventory import InventoryItem

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5

BYTEORDER: Literal['little', 'big'] = "big"


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
    old_inventory = set(old_inventory.values())
    new_inventory = set(new_inventory.values())

    return old_inventory - new_inventory
