import logging

import state
from utils import BufferWriter, BufferReader
from packets.packet import NetworkPacket

import enum

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


def handle(packet: Response):
    if packet.status == LoginStatus.SUCCESS or packet.status == LoginStatus.SUCCESS_NEW_USER:
        logging.info(f"Logged in as player {packet.player_id}")

        state.logged_in = True
    else:
        logging.info(f"Login failed with status {packet.status.name}")


receive_packet = Response
