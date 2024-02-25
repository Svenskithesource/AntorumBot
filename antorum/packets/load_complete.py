from antorum.packets import NetworkPacket

packet_id = 2


class Request(NetworkPacket):
    packet_id = packet_id

    def __init__(self):
        pass

    def serialize(self):
        return b""
