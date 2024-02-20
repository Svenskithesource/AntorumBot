import enum
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from packets import NetworkPacket
from utils import BufferReader

if TYPE_CHECKING:
    import multiplayer

packet_id = 43


class BarterInventoryItemArea(enum.Enum):
    INVENTORY = 0
    YOU_OFFER = 1
    STORE_INVENTORY = 2
    STORE_OFFER = 3


@dataclass
class BarterOpen:
    inventory_values: dict
    shop_items: dict
    buys_items: bool
    sells_items: bool
    shop_name: str


@dataclass
class Barter:
    inventory_items: dict
    you_offer: dict
    store_items: dict
    store_offer: dict


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)

        inventory_values = {reader.read_int8(): reader.read_int32() for _ in
                            range(reader.read_int64())}  # second item is the value of the item

        shop_items = {reader.read_int64(): (reader.read_int32(), reader.read_int32()) for _ in
                      range(reader.read_int64())}  # second item is the amount and third is the value

        buys_items = reader.read_bool()
        sells_items = reader.read_bool()
        shop_name = reader.read_string()

        self.barter = BarterOpen(inventory_values, shop_items, buys_items, sells_items, shop_name)


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received barter_open packet: {packet.barter}")

    client.game.barter = Barter(packet.barter.inventory_values, {}, packet.barter.shop_items, {})


receive_packet = Response
