import enum
import json
import logging
from dataclasses import dataclass
from typing import Tuple, List, Dict

from packets import NetworkPacket
from utils import BufferReader

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

            equipped = {}
            for _ in range(reader.read_int64()):
                slot = ItemSlot(reader.read_int8())
                resource_id = reader.read_int64()  # TODO: Make a resource list to look up the resource
                amount = reader.read_int32()
                text = reader.read_string()
                parsed = json.loads(text if text.strip() else "{}")
                property_bag = ItemPropertyBag(**parsed)
                equipped[slot] = InventoryItem(None, amount, property_bag)

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


class Entity:
    def __init__(self, reader: BufferReader):
        self.network_id = reader.read_int64()

        self.states = []

        amount = reader.read_int64()
        for i in range(amount):
            self.states.append(EntityState(reader))


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
        self.entities = self.read_entities(reader)
        self.removed_entities = [reader.read_int64() for _ in range(reader.read_int64())]
        self.full_sync = reader.read_bool()


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received {len(packet.entities)} entities, at coords {packet.coords}")
    logging.debug(f"Removed {len(packet.removed_entities)} entities")
    logging.debug(f"Full sync: {packet.full_sync}")
    for entity in packet.entities:
        logging.debug(f"Entity {entity.network_id} with {len(entity.states)} states")
        for state in entity.states:
            logging.debug(f"State: {state.state}")


receive_packet = Response
