from player import Player


class Game:
    def __init__(self, local_player_id: int, network_id: int):
        self.local_player_id = local_player_id
        self.network_id = network_id
        self.local_player: Player = None
        self.entities = {}
