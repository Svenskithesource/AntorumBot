from typing import TYPE_CHECKING

from packets import NetworkPacket
from packets.barter_open import BarterInventoryItemArea
from utils import BufferReader, BufferWriter

if TYPE_CHECKING:
    import multiplayer

packet_id = 47


class Request(NetworkPacket):
    packet_id = 46

    def __init__(self, source_area: BarterInventoryItemArea, slot: int, amount: int):
        self.source_area = source_area
        self.slot = slot
        self.amount = amount

    def serialize(self) -> bytes:
        writer = BufferWriter()

        writer.write_int8(self.source_area.value)
        writer.write_int8(self.slot)
        writer.write_int32(self.amount)

        return bytes(writer)


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)

        self.shopper_coin_value = reader.read_int32()
        self.shop_coin_value = reader.read_int32()
        self.source_area = BarterInventoryItemArea(reader.read_int8())
        self.moved = []
        for _ in range(reader.read_int64()):
            self.moved.append((reader.read_int8(), reader.read_int8(), reader.read_int32()))


def handle(packet: Response, client: "multiplayer.Client"):
    if packet.source_area == BarterInventoryItemArea.INVENTORY:
        client.game.barter.you_offer = {slot: (item, amount) for slot, item, amount in packet.moved}

        for slot, _, _ in packet.moved:
            client.game.barter.inventory_items.pop(slot, None)
    elif packet.source_area == BarterInventoryItemArea.YOU_OFFER:
        client.game.barter.inventory_items = {slot: (item, amount) for slot, item, amount in packet.moved}

        for slot, _, _ in packet.moved:
            client.game.barter.you_offer.pop(slot, None)
    elif packet.source_area == BarterInventoryItemArea.STORE_INVENTORY:
        client.game.barter.store_offer = {slot: (item, amount) for slot, item, amount in packet.moved}

        for slot, _, _ in packet.moved:
            client.game.barter.store_items.pop(slot, None)
    elif packet.source_area == BarterInventoryItemArea.STORE_OFFER:
        client.game.barter.store_items = {slot: (item, amount) for slot, item, amount in packet.moved}

        for slot, _, _ in packet.moved:
            client.game.barter.store_offer.pop(slot, None)


receive_packet = Response
