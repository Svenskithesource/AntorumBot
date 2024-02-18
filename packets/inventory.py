import logging
from typing import Dict

from packets import NetworkPacket
from packets.inventory_add import Response as InventoryAdd
from packets.inventory_add import InventoryItem
from utils import BufferReader
from cache import resources

packet_id = 19


class Response(NetworkPacket):
    packet_id = packet_id

    def parse(self, reader: BufferReader):
        self.items = {}
        for _ in range(reader.read_int64()):
            item = InventoryAdd()
            item.parse(reader)

            self.items[item.index] = InventoryItem(resources[item.resource_id], item.amount, item.property_bag)

        return self.items

    def __init__(self, data: bytes = b""):
        self.items: Dict[int, InventoryItem] = {}
        self.parse(BufferReader(data))


def handle(packet: Response, client: "multiplayer.Client"):
    if client._loaded < 2:
        client._loaded += 1

    logging.debug(f"Received inventory: {packet.items}")
    client.game.local_player.inventory = packet.items


receive_packet = Response
