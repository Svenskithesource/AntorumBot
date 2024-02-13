class NetworkPacket:
    header_size: int = 3
    packet_id: int

    def serialize(self):
        pass

    def __str__(self):
        return f"{self.__class__.__name__}({self.__dict__})"
