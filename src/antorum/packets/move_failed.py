import logging
from typing import TYPE_CHECKING

from antorum.packets import NetworkPacket

if TYPE_CHECKING:
    from antorum import multiplayer

packet_id = 85


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        pass


def handle(packet: Response, client: "multiplayer.Client"):
    logging.info("Move failed")


receive_packet = Response
