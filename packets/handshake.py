import base64
import enum
import logging

from packets.packet import NetworkPacket
from utils import BYTEORDER, BufferReader

packet_id = 0


class HandshakeStatus(enum.Enum):
    ACCEPTED = 0
    REJECTED = 1
    ACCEPTEDNEEDSDOWNLOAD = 2


class Packet(NetworkPacket):
    packet_id = packet_id

    def __init__(self, protocol: int = 12, world: int = 0, item_cache: int = 0, enchantment_cache: int = 0):
        self.protocol = protocol
        self.world = world
        self.item_cache = item_cache
        self.enchantment_cache = enchantment_cache

    def __bytes__(self):
        return self.serialize()

    def serialize(self):
        return (self.protocol.to_bytes(2, BYTEORDER)
                + self.world.to_bytes(4, BYTEORDER)
                + self.item_cache.to_bytes(8, BYTEORDER)
                + self.enchantment_cache.to_bytes(8, BYTEORDER))


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.status = HandshakeStatus(reader.read_int8())
        self.player_count = reader.read_int32()
        self.encryption_key = base64.b64decode(reader.read_string())
        self.latest_news = reader.read_string()


def handle(packet: Response):
    if packet.status == HandshakeStatus.REJECTED:
        logging.error("Handshake rejected")
        exit(1)

    logging.info(f"Handshake accepted, {packet.player_count} players online. Latest news:\n{packet.latest_news}")


receive_packet = Response
