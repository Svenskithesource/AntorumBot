import enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, TYPE_CHECKING

from packets.inventory import ItemSlot, InventoryItem
from packets.stats import Stat

if TYPE_CHECKING:
    import multiplayer


class SkillType(enum.Enum):
    FISHING = 0
    COOKING = 1
    HERBOLOGY = 2
    COMBAT = 3
    DEFENSE = 4
    ATHLETICS = 5
    SALVAGING = 6
    GEARCRAFTING = 7
    RITUAL = 8
    MINING = 9


@dataclass
class Skill:
    type: SkillType
    level: int
    experience: int
    exp_current_level: int
    exp_next_level: int


class Player:
    def __init__(self, player_id: int, network_id: int, skills: List[Skill] = None, health: int = 30,
                 max_health: int = 30, username: str = "Unknown", position: Tuple[float, float] = (-1, -1),
                 stats: Dict[Stat, int] = None, inventory: List[Tuple[ItemSlot, InventoryItem]] = None):
        if inventory is None:
            inventory = {}

        if stats is None:
            stats = {}

        if skills is None:
            skills = []
        self.player_id = player_id
        self.network_id = network_id
        self.skills = skills
        self.stats = stats
        self.health = health
        self.max_health = max_health
        self.position = position
        self.inventory = inventory
        self.username = username

    def __str__(self):
        return f"{self.username} ({self.health}/{self.max_health}) at {self.position}"
