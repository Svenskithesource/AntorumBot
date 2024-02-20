import enum
import logging
import datetime
from dataclasses import dataclass

from packets import NetworkPacket
from utils import BufferReader, get_entity_from_player_id, StateType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiplayer

packet_id = 5


class ChatChannel(enum.Enum):
    SYSTEM = 0
    COMBAT = 1
    LOCAL = 2
    ALL = 3
    PARTY = 4


@dataclass
class ChatMessage:
    player_id: int
    username: str
    channel: ChatChannel
    message: str


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.message = ChatMessage(reader.read_int64(), reader.read_string(), ChatChannel(reader.read_int8()),
                                   reader.read_string())


def handle(packet: Response, client: "multiplayer.Client"):
    if client.game:  # First chat packet is received before the game is initialized
        if not packet.message.username:
            entity = get_entity_from_player_id(packet.message.player_id, list(client.game.entities.values()))
            if entity:
                packet.message.username = entity.states[StateType.INFO].state.name

        if len(client.game.chat_log) > 1000:
            client.game.chat_log = client.game.chat_log[500:]  # Remove the first 500 messages to prevent memory leaks

        client.game.chat_log.append((datetime.datetime.now(), packet.message))

    logging.info(f"({packet.message.channel.name}) {packet.message.username}: {packet.message.message}")


receive_packet = Response
