from utils import BufferWriter, BufferReader
import logging
import enum

from packets.packet import NetworkPacket

packet_id = 49  # the creation is 48 but the response is 49


class CreationStatus(enum.Enum):
    SUCCESS = 0
    INVALID_CLASS = 1
    INVALID_STATS = 2
    INVALID_BODY = 3
    INVALID_NAME = 4
    NAME_TAKEN = 5


class Packet(NetworkPacket):
    packet_id = 48

    def __init__(self, name: str, crafting_skill: int, foraging_skill: int, combat_skill: int,
                 ascetic_skill: int, stamina: int, strength: int, smarts: int, speed: int, hair: int, hair_color: int,
                 facial_hair: int, facial_hair_color: int, skin_color: int, shirt: int, pants: int, bulk: int,
                 height: int):
        self.name = name
        self.crafting_skill = crafting_skill
        self.foraging_skill = foraging_skill
        self.combat_skill = combat_skill
        self.ascetic_skill = ascetic_skill
        self.stamina = stamina
        self.strength = strength
        self.smarts = smarts
        self.speed = speed
        self.hair = hair
        self.hair_color = hair_color
        self.facial_hair = facial_hair
        self.facial_hair_color = facial_hair_color
        self.skin_color = skin_color
        self.shirt = shirt
        self.pants = pants
        self.bulk = bulk
        self.height = height

    def serialize(self):
        writer = BufferWriter()

        writer.write_string(self.name)
        writer.write_int8(self.crafting_skill)
        writer.write_int8(self.foraging_skill)
        writer.write_int8(self.combat_skill)
        writer.write_int8(self.ascetic_skill)
        writer.write_int8(self.stamina)
        writer.write_int8(self.strength)
        writer.write_int8(self.smarts)
        writer.write_int8(self.speed)
        writer.write_int8(self.hair)
        writer.write_int8(self.hair_color)
        writer.write_int8(self.facial_hair)
        writer.write_int8(self.facial_hair_color)
        writer.write_int8(self.skin_color)
        writer.write_int8(self.shirt)
        writer.write_int8(self.pants)
        writer.write_int8(self.bulk)
        writer.write_int8(self.height)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.status = CreationStatus(reader.read_int8())


def handle(self, client: "multiplayer.Client"):
    if self.status == CreationStatus.SUCCESS:
        logging.info(f"Character created!")
    else:
        logging.error(f"Character creation failed: {self.status.name}")


receive_packet = Response
