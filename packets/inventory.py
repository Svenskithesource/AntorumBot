import enum
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from packets import NetworkPacket
from packets.item import ItemResource, ItemPropertyBag, ItemSlot
from utils import BufferReader
from cache import resources

packet_id = 19


@dataclass
class InventoryItem:
    resource: ItemResource
    amount: int
    property_bag: ItemPropertyBag


class Response(NetworkPacket):
    packet_id = packet_id

    def parse(self, reader: BufferReader):
        self.items = []
        for _ in range(reader.read_int64()):
            slot = ItemSlot(reader.read_int8())
            resource_id = reader.read_int64()
            amount = reader.read_int32()
            text = reader.read_string()
            parsed = json.loads(text if text.strip() else "{}")
            property_bag = ItemPropertyBag(**parsed)
            self.items.append((slot, InventoryItem(resources[resource_id], amount, property_bag)))

        return self.items

    def __init__(self, data: bytes = b""):
        self.items: List[Tuple[ItemSlot, InventoryItem]] = []
        self.parse(BufferReader(data))


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received inventory: {packet.items}")
    client.game.local_player.inventory = packet.items


receive_packet = Response
