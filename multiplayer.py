import asyncio
import base64

import packets
import logging

import utils
from utils import BYTEORDER, BufferWriter
import state


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

    async def login(self, username: str, password: str):
        if state.logged_in:
            logging.warning("Already logged in")
            return

        while not state.handshake_established:
            await asyncio.sleep(0.1)

        logging.info(f"Logging in as {username}")
        self.send_queue.put_nowait(
            packets.Login(username, utils.EncryptionHelper(state.encryption_key).encrypt(password.encode("utf-8"))))

    async def send(self, data: packets.NetworkPacket):
        serialized = data.serialize()
        writer = BufferWriter()

        writer.write_int16(len(serialized))
        writer.write_int8(data.packet_id)
        writer.write(serialized)

        self.writer.write(bytes(writer))

        logging.debug(f"Serialized data: {'-'.join(hex(n)[2:].zfill(2) for n in bytes(writer))}")
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
        while True:
            await asyncio.sleep(0.1)
            while self.recv_queue.qsize() > 0:
                packet_id, data = await self.recv_queue.get()

                logging.debug(f"Received packet {packet_id} with data {data}")

                handler = packets.get_handler(packet_id)

                if handler:
                    handler(data)

            while self.send_queue.qsize() > 0:
                data = await self.send_queue.get()

                logging.debug(f"Sending packet {data.packet_id} with data {data}")

                await self.send(data)
