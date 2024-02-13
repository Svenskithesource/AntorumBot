import base64
import enum
import logging

import state
from packets.packet import NetworkPacket
from utils import BYTEORDER, BufferReader, BufferWriter

packet_id = 0


class HandshakeStatus(enum.Enum):
    ACCEPTED = 0
    REJECTED = 1
    ACCEPTEDNEEDSDOWNLOAD = 2


class Packet(NetworkPacket):
    packet_id = packet_id

    def __init__(self, protocol: int = 12, world: int = 0x44F, item_cache: int = 9967626288493068445,
                 enchantment_cache: int = 16519598071320280894):
        self.protocol = protocol
        self.world = world
        self.item_cache = item_cache
        self.enchantment_cache = enchantment_cache

    def __bytes__(self):
        return self.serialize()

    def serialize(self):
        writer = BufferWriter()

        writer.write_int16(self.protocol)
        writer.write_int32(self.world)
        writer.write_int64(self.item_cache)
        writer.write_int64(self.enchantment_cache)

        return bytes(writer)


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
    logging.debug(f"Encryption key: {packet.encryption_key}")
    state.encryption_key = packet.encryption_key
    state.handshake_established = True


receive_packet = Response
