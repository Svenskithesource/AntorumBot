from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from antorum.packets.world_entities import Entity
    from antorum.packets.barter_open import Barter
    from antorum.packets.inventory_add import ItemResource

from antorum.player import Player
from antorum.cache import resources


class Game:
    def __init__(self, local_player_id: int, network_id: int):
        self.local_player_id = local_player_id
        self.network_id = network_id
        self.local_player: Player = Player(local_player_id, network_id)
        self.entities: Dict[int, "Entity"] = {}
        self.resources: Dict[int, "ItemResource"] = resources
        self.chat_log = []

        self.barter: "Barter" = None
