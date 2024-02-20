from typing import Dict, TYPE_CHECKING

from packets.inventory_add import ItemResource

if TYPE_CHECKING:
    from packets.world_entities import Entity
    import multiplayer

from player import Player
from cache import resources


class Game:
    def __init__(self, local_player_id: int, network_id: int):
        self.local_player_id = local_player_id
        self.network_id = network_id
        self.local_player: Player = Player(local_player_id, network_id)
        self.entities: Dict[int, Entity] = {}
        self.resources: Dict[int, ItemResource] = resources
        self.chat_log = []
