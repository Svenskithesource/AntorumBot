import os
from pathlib import Path

from antorum.packets.handshake import Packet as Handshake
from antorum.packets.login import Packet as Login
from antorum.packets.packet import NetworkPacket
from antorum.packets.load_complete import Request as LoadComplete
from antorum.packets.move import Packet as Move
from antorum.packets.interact import Packet as Interact
from antorum.packets.inventory_read_item import Request as InventoryReadItem
from antorum.packets.inventory_item_drop import Request as InventoryItemDrop
from antorum.packets.barter_move import Request as BarterMove
from antorum.packets.barter_close import Request as BarterClose

handlers = {}

for module in os.listdir(Path(__file__).parent):
    if module.startswith("_"):
        continue

    m = __import__(f"antorum.packets.{module[:-3]}", fromlist=[""])
    if hasattr(m, "packet_id"):
        handlers[m.packet_id] = m


def get_handler(packet_id: int):
    module = handlers.get(packet_id)
    if module is None:
        return None

    return lambda data, client: module.handle(module.receive_packet(data), client)
