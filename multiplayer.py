import asyncio
import packets
import logging
from utils import BYTEORDER


class Client:
    def __init__(self, host: str = "antorum.game.ratwizard.dev", port: int = 7667):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.send_queue = asyncio.Queue()
        self.recv_queue = asyncio.Queue()

    async def connect(self):
        logging.info(f"Connecting to {self.host}:{self.port}")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info("Connected!")

        asyncio.create_task(self.recv_loop())

        logging.info("Sending handshake")
        self.send_queue.put_nowait(packets.Handshake())

    async def send(self, data: packets.NetworkPacket):
        serialized = data.serialize()
        to_send = len(serialized).to_bytes(2, BYTEORDER) + data.packet_id.to_bytes(1, BYTEORDER) + serialized
        self.writer.write(to_send)
        await self.writer.drain()

    async def recv_loop(self):
        while True:
            data = await self.reader.read(3)

            while len(data) != 3:
                data += await self.reader.read(1)

            packet_size = int.from_bytes(data[:2], BYTEORDER)
            packet_id = data[2]

            data = await self.reader.read(packet_size)
            while len(data) < packet_size:
                data += await self.reader.read(packet_size - len(data))

            self.recv_queue.put_nowait((packet_id, data))

    async def update(self):
        while self.recv_queue.qsize() > 0:
            packet_id, data = await self.recv_queue.get()

            logging.debug(f"Received packet {packet_id} with data {data}")

            handler = packets.get_handler(packet_id)

            if handler:
                handler(data)

        while self.send_queue.qsize() > 0:
            data = await self.send_queue.get()
            await self.send(data)
