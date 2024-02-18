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

        self.is_following = False

        self.game: Game = None

    async def connect(self):
        logging.info(f"Connecting to {self.host}:{self.port}")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info("Connected!")

        asyncio.create_task(self.recv_loop())

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
        while not self.game or not self.game.entities:
            await asyncio.sleep(0.01)
        self.send_queue.put_nowait(packets.LoadComplete())  # Server needs two of these for some reason
        logging.info("Game loaded!")

    async def move(self, x: float, y: float):
        logging.info(f"Moving to {x}, {y}")
        self.send_queue.put_nowait(packets.Move(x, y))

    async def follow(self, network_id: int):
        logging.debug(f"Following entity {network_id}")
        self.is_following = True
        original_position = utils.get_future_position_from_entity(network_id, self.game)

        if original_position != self.game.local_player.position:
            await self.move(*original_position)

        while True:
            if not self.is_following:
                break

            if original_position != utils.get_future_position_from_entity(network_id, self.game):
                original_position = utils.get_future_position_from_entity(network_id, self.game)
                await self.move(original_position[0], original_position[1])

            await asyncio.sleep(0.01)

    async def follow_player(self, username: str):
        logging.info(f"Following player {username}")
        network_id = utils.get_entity_from_player_id(utils.get_player_id_from_username(username, self.game),
                                                     self.game.entities.values()).network_id

        if network_id:
            await self.follow(network_id)
        else:
            logging.error(f"Player {username} not found")

    async def stop_following(self):
        logging.info("Stopping follow")
        self.is_following = False

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

            logging.debug("Received packet, adding to queue")

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
