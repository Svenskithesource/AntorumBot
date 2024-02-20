import logging

from packets import NetworkPacket
from player import SkillType, Skill
from utils import BufferReader

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiplayer

packet_id = 17


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.skills = {}
        for _ in range(reader.read_int64()):
            skill_type = SkillType(reader.read_int8())
            experience = reader.read_int32()
            level = reader.read_int32()
            current_level_exp = reader.read_int32()
            next_level_exp = reader.read_int32()

            self.skills[skill_type] = Skill(skill_type, level, experience, current_level_exp, next_level_exp)


def handle(packet: Response, client: "multiplayer.Client"):
    if client._loaded < 3:  # Skills is part of the necessary packets to be loaded
        client._loaded += 1

    client.game.local_player.skills = packet.skills


receive_packet = Response
