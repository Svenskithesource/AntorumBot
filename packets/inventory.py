import enum
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from packets import NetworkPacket
from utils import BufferReader

packet_id = 19


class ItemSlot(enum.Enum):
    NONE = 0
    main_hand = 1
    off_hand = 2
    head = 3
    torso = 4
    legs = 5


class ItemType(enum.Enum):
    MISC = 1
    CONSUMABLE = 2
    INGREDIENT = 4
    CURRENCEY = 8
    WEAPON = 16
    ARMOR = 32
    TOOL = 64


@dataclass
class ItemAttributes:
    damage: int
    armor: int
    heal_amount: int
    ingredient_slots: int
    equipment_slot: ItemSlot
    can_block: bool
    can_fish: bool
    can_cast_rituals: bool
    can_craft: bool
    can_mine: bool
    hide_hair: bool


class ItemResource:
    def __init__(self, reader: BufferReader):
        self.resource_id = reader.read_int64()
        self.resource_name = reader.read_string()
        self.name = reader.read_string()
        self.plural_name = reader.read_string()
        self.item_type = ItemType(reader.read_int8())
        self.model_id = reader.read_int16()
        self.dropped_model_id = reader.read_int16()
        self.value = reader.read_int32()
        self.is_tradeable = reader.read_bool()
        self.effect_id = reader.read_int64()
        self.item_attributes = ItemAttributes(reader.read_int32(), reader.read_int32(), reader.read_int32(),
                                              reader.read_int32(), ItemSlot(reader.read_int8()), reader.read_bool(),
                                              reader.read_bool(), reader.read_bool(), reader.read_bool(),
                                              reader.read_bool(), reader.read_bool())


@dataclass
class ItemPropertyBag:
    durability: int = -1
    max_durability: int = -1
    creator: str = ""
    enchantment_id: int = -1


@dataclass
class InventoryItem:
    resource: ItemResource
    amount: int
    property_bag: ItemPropertyBag


class Response(NetworkPacket):
    packet_id = packet_id

    def parse(self, reader: BufferReader):
        self.items = []
        for _ in range(reader.read_int64()):
            slot = ItemSlot(reader.read_int8())
            resource_id = reader.read_int64()  # TODO: Make a resource list to look up the resource
            amount = reader.read_int32()
            text = reader.read_string()
            parsed = json.loads(text if text.strip() else "{}")
            property_bag = ItemPropertyBag(**parsed)
            self.items.append((slot, InventoryItem(resource_id, amount, property_bag)))

        return self.items

    def __init__(self, data: bytes = b""):
        self.items: List[Tuple[ItemSlot, InventoryItem]] = []
        self.parse(BufferReader(data))


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received inventory: {packet.items}")
    client.game.local_player.inventory = packet.items


receive_packet = Response
