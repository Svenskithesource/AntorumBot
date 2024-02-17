from packets import NetworkPacket
from utils import BufferReader

packet_id = 9


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.network_id = reader.read_int64()


def handle(packet: Response, client: "multiplayer.Client"):
    client.game.entities.pop(packet.network_id, None)


receive_packet = Response
