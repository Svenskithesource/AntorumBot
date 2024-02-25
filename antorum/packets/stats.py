import enum
import logging
from typing import TYPE_CHECKING

from antorum.packets import NetworkPacket
from antorum.utils import BufferReader

if TYPE_CHECKING:
    from antorum import multiplayer

packet_id = 18


class Stat(enum.Enum):
    STAMINA = 0
    STRENGTH = 1
    SMARTS = 2
    SPEED = 3
    ARMOR = 4
    DAMAGE = 5
    MAX_HEALTH = 6
    SPEED_BONUS = 7


class StatBonuses:
    def __init__(self, reader: BufferReader):
        self.base_hp = reader.read_int32()
        self.base_hit_chance = reader.read_float()
        self.base_dodge_chance = reader.read_float()
        self.base_block_chance = reader.read_float()
        self.skill_success_bonus = reader.read_float()


class ClassBonuses:
    def __init__(self, reader: BufferReader):
        self.crafting_exp_bonus = reader.read_float()
        self.foraging_exp_bonus = reader.read_float()
        self.combat_exp_bonus = reader.read_float()


class Response(NetworkPacket):
    packet_id = packet_id

    def __init__(self, data: bytes):
        reader = BufferReader(data)
        self.stats = {Stat(reader.read_int8()): reader.read_int32() for _ in range(reader.read_int64())}
        self.bonuses = StatBonuses(reader)
        self.class_bonuses = ClassBonuses(reader)

        # Spell effects, not implemented yet
        for _ in range(reader.read_int64()):
            reader.read_int64(), reader.read_string(), reader.read_string(), reader.read_int64()
            reader.read_int32(), reader.read_int32(), reader.read_bool()


def update_stat(stat, value, client: "multiplayer.Client"):
    client.game.local_player.stats[stat] = value


def update_stats(stats, client: "multiplayer.Client"):
    for stat, value in stats.items():
        update_stat(stat, value, client)


def handle(packet: Response, client: "multiplayer.Client"):
    logging.debug(f"Received stats: {packet.stats}")
    update_stats(packet.stats, client)


receive_packet = Response
