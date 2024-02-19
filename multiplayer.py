import asyncio

import packets
import logging

import utils
from game import Game
from utils import BYTEORDER, BufferWriter


class Client:
    def __init__(self, host: str = "antorum.game.ratwizard.dev", port: int = 7667):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.send_queue = asyncio.Queue()
        self.recv_queue = asyncio.Queue()

        self.handshake_established = False
        self.logged_in = False
        self.encryption_key = ""
        self.player_id = -1

        self._loaded = 0  # counter to check if necessary packets are received, 2 means the client is loaded

        self.game: Game = None

    @property
    def loaded(self):
        return self._loaded == 2

    async def connect(self):
        logging.info(f"Connecting to {self.host}:{self.port}")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info("Connected!")

        asyncio.get_event_loop().create_task(self.recv_loop())

        logging.info("Sending handshake")
        self.send_queue.put_nowait(packets.Handshake())

    async def login(self, username: str, password: str):
        if self.logged_in:
            logging.warning("Already logged in")
            return

        while not self.handshake_established:
            await asyncio.sleep(0.1)

        logging.info(f"Logging in as {username}")
        self.send_queue.put_nowait(
            packets.Login(username, utils.EncryptionHelper(self.encryption_key).encrypt(password.encode("utf-8"))))

    async def load_game(self):
        if not self.logged_in:
            logging.error("Not logged in")
            return

        logging.info("Loading game")
        self.send_queue.put_nowait(packets.LoadComplete())
        while not self.loaded:
            await asyncio.sleep(0.01)
        self.send_queue.put_nowait(packets.LoadComplete())  # Server needs two of these for some reason
        logging.info("Game loaded!")

    async def move(self, x: float, y: float):
        logging.info(f"Moving to {x}, {y}")
        self.send_queue.put_nowait(packets.Move(x, y))

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
            await asyncio.sleep(0.01)
            while self.recv_queue.qsize() > 0:
                packet_id, data = await self.recv_queue.get()

                logging.debug(f"Received packet {packet_id} with data {data}")

                handler = packets.get_handler(packet_id)

                if handler:
                    handler(data, self)

            while self.send_queue.qsize() > 0:
                data = await self.send_queue.get()

                logging.debug(f"Sending packet {data.packet_id} with data {data}")

                await self.send(data)
