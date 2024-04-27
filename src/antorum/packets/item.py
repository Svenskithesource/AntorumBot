import enum
from dataclasses import dataclass

from antorum.utils import BufferReader


class ItemSlot(enum.Enum):
    NONE = 0
    main_hand = 1
    off_hand = 2
    head = 3
    torso = 4
    legs = 5


class ItemType(enum.Flag):
    MISC = 1
    CONSUMABLE = 2
    INGREDIENT = 4
    CURRENCY = 8
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

    def __repr__(self):
        return f"ItemResource({repr(self.resource_id)}, {repr(self.resource_name)}, {repr(self.name)}, " \
               f"{repr(self.plural_name)}, {repr(self.item_type)}, {repr(self.model_id)}, {repr(self.dropped_model_id)}, " \
               f"{repr(self.value)}, {repr(self.is_tradeable)}, {repr(self.effect_id)}, {repr(self.item_attributes)})"

    def __str__(self):
        return f"ItemResource({self.resource_id}, {self.resource_name}, {self.name}, {self.plural_name}, {self.item_type}, " \
               f"{self.model_id}, {self.dropped_model_id}, {self.value}, {self.is_tradeable}, {self.effect_id}, " \
               f"{self.item_attributes})"


@dataclass
class ItemPropertyBag:
    durability: int = -1
    max_durability: int = -1
    creator: str = ""
    enchantment_id: int = -1
