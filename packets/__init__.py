import os
from pathlib import Path

from packets.handshake import Packet as Handshake
from packets.login import Packet as Login
from packets.packet import NetworkPacket
from packets.load_complete import Request as LoadComplete
from packets.move import Packet as Move

handlers = {}

for module in os.listdir(Path(__file__).parent):
    if module.startswith("_"):
        continue

    m = __import__(f"packets.{module[:-3]}", fromlist=[""])
    if hasattr(m, "packet_id"):
        handlers[m.packet_id] = m


def get_handler(packet_id: int):
    module = handlers.get(packet_id)
    if module is None:
        return None

    handler = lambda data, client: module.handle(module.receive_packet(data), client)
    return handler
