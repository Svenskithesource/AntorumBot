import logging
from typing import TYPE_CHECKING

from antorum.utils import BufferWriter, BufferReader
from antorum.packets.packet import NetworkPacket
from antorum.packets.character_creation import Packet as CharacterCreationPacket

import enum

if TYPE_CHECKING:
    from antorum import multiplayer

packet_id = 1


class LoginStatus(enum.Enum):
    SUCCESS = 0
    ERROR = 1
    INVALID_CREDS = 2
    SERVER_FULL = 3
    REJECTED = 4
    ALREADY_LOGGED_IN = 5
    SUCCESS_NEW_USER = 6


class Packet(NetworkPacket):
    packet_id = packet_id

    def __init__(self, username: str, encrypted_password: bytes):
        self.username = username
        self.encrypted_password = encrypted_password

    def serialize(self):
        writer = BufferWriter()

        writer.write_string(self.username)
        writer.write_bytes(self.encrypted_password)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.status = LoginStatus(reader.read_int8())
        self.player_id = reader.read_int64()


def handle(packet: Response, client: "multiplayer.Client"):
    if packet.status == LoginStatus.SUCCESS or packet.status == LoginStatus.SUCCESS_NEW_USER:
        logging.info(f"Logged in as player {packet.player_id}")
        client.player_id = packet.player_id
        client.logged_in = True

        if packet.status == LoginStatus.SUCCESS_NEW_USER:
            logging.info("No existing character, creating a new one")
            name = input("Character name: ")

            crafting_skill = int(input("Crafting skill (0 - 5, default 0): "))
            foraging_skill = int(input("Foraging skill (0 - 5, default 0): "))
            combat_skill = int(input("Combat skill (0 - 5, default 0): "))
            ascetic_skill = int(input("Ascetic skill (0 - 5, default 0): "))

            stamina = int(input("Stamina (0 - 10, default 0): "))
            strength = int(input("Strength (0 - 10, default 0): "))
            smarts = int(input("Smarts (0 - 10, default 0): "))
            speed = int(input("Speed (0 - 10, default 0): "))

            hair = int(input("Hair (0 - 12, default 0): "))
            hair_color = int(input("Hair color (0 - 10, default 0): "))
            facial_hair = int(input("Facial hair (0 - 6, default 0): "))
            facial_hair_color = int(input("Facial hair color (0 - 10, default 0): "))
            skin_color = int(input("Skin color (0 - 35, default 0): "))
            shirt = int(input("Shirt (0 - 28, default 0): "))
            pants = int(input("Pants (0 - 28, default 0): "))
            bulk = int(input("Bulk (0 - 5, default 0): "))
            height = int(input("Height (0 - 5, default 0): "))

            client.send_queue.put_nowait(
                CharacterCreationPacket(name, crafting_skill, foraging_skill, combat_skill, ascetic_skill,
                                        stamina, strength, smarts, speed, hair, hair_color, facial_hair,
                                        facial_hair_color, skin_color, shirt, pants, bulk, height))
    else:
        logging.info(f"Login failed with status {packet.status.name}")


receive_packet = Response
