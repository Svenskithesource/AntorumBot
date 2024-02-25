import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from antorum import multiplayer

from antorum.packets import NetworkPacket
from antorum.packets.item import ItemPropertyBag, ItemResource
from antorum.utils import BufferReader

packet_id = 20


@dataclass
class InventoryItem:
    resource: ItemResource
    amount: int
    property_bag: ItemPropertyBag


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes = b""):
        reader = BufferReader(data)
        self.parse(reader)

    def parse(self, reader: BufferReader):
        self.index = reader.read_int8()
        self.resource_id = reader.read_int64()
        self.amount = reader.read_int32()
        text = reader.read_string()
        parsed = json.loads(text if text.strip() else "{}")
        self.property_bag = ItemPropertyBag(**parsed)


def handle(packet: Response, client: "multiplayer.Client"):
    if packet.index in client.game.local_player.inventory.keys():
        if packet.resource_id == client.game.local_player.inventory[packet.index].resource.resource_id:
            client.game.local_player.inventory[packet.index].amount += packet.amount
        else:
            client.game.local_player.inventory[packet.index] = InventoryItem(client.game.resources[packet.resource_id],
                                                                             packet.amount, packet.property_bag)
    else:
        client.game.local_player.inventory[packet.index] = InventoryItem(client.game.resources[packet.resource_id],
                                                                         packet.amount,
                                                                         packet.property_bag)

    logging.info(
        f"Adding {packet.amount} {client.game.resources[packet.resource_id].name} to inventory (index {packet.index})")


receive_packet = Response
