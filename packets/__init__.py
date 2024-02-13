import os
from pathlib import Path

from packets.handshake import Packet as Handshake
from packets.packet import NetworkPacket

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

    handler = lambda data: module.handle(module.receive_packet(data))
    return handler
