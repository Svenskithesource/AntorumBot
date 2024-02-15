from typing import Dict

from packets.inventory import ItemResource
from player import Player
from cache import resources


class Game:
    def __init__(self, local_player_id: int, network_id: int):
        self.local_player_id = local_player_id
        self.network_id = network_id
        self.local_player: Player = None
        self.entities = {}
        self.resources: Dict[int, ItemResource] = resources
