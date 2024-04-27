import logging

from antorum.packets import NetworkPacket
from antorum.player import SkillType
from antorum.utils import BufferReader

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from antorum import multiplayer

packet_id = 15


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()
        self.skill_type = SkillType(reader.read_int8())
        self.exp = reader.read_int32()


def handle(packet: Response, client: "multiplayer.Client"):
    if packet.network_id == client.game.local_player.network_id:
        client.game.local_player.skills[packet.skill_type].experience += packet.exp
        logging.info(
            f"+{packet.exp} {packet.skill_type.name} experience ({client.game.local_player.skills[packet.skill_type].experience})")


receive_packet = Response
