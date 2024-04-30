# Antorum Bot

Antorum Bot is a package that allows you to create a bot for the game [Antorum](https://antorum.ratwizard.dev/).
It is made by reverse engineering the game's network activity and is not officially supported by the game's developers.

## Usage
To use the bot, you need to install the package (`pip install antorum`) and create a new bot instance.

```python
from antorum import multiplayer
import asyncio


async def main():  # The bot must be ran asynchronously
    client = multiplayer.Client()

    await client.connect()  # Establish a connection to the game server

    await client.login("username", "password")  # Log in to the game with your credentials

    while not client.logged_in:
        await asyncio.sleep(0.1)  # Wait for the client to log in

    await client.load_game()  # Load all the entities in the game

    print("Playing as " + client.game.local_player.username)
```

### Actions
I came up with the concept of actions. The idea is that you can use existing actions, or create your own.
Here's an example of how to use an action:

```python
from antorum import multiplayer, actions
import asyncio

async def main():
    # See the previous example for the setup

    while True:
        forage = actions.ForageWeeds(client)
        await forage.run() # Run the action

        await forage.wait_to_finish() # Wait for the action to finish, this will run until the inventory is full

        sell = actions.SellInventory(client, "skartweed") # Sell all skartweed (the item it foraged) in the inventory
        await sell.run()

        await sell.wait_to_finish()
```

### Custom Actions
You can create your own actions by subclassing `actions.Action` and implementing the `_run` method.
Here's an example of a custom action that follows a player:

```python
class FollowPlayer(Action):
    def __init__(self, client: "multiplayer.Client", username: str):
        super().__init__(client)
        self.username = username # The username of the player to follow

    async def follow(self, network_id: int):
        logging.debug(f"Following entity {network_id}")
        
        # Get the player's position, if it's moving it will grab the final destination
        original_position = utils.get_future_position_from_entity(network_id, self.client.game)

        if original_position != self.client.game.local_player.position: # Move to the player if we're not already there
            await self.client.move(*original_position)

        while True:
            if original_position != utils.get_future_position_from_entity(network_id, self.client.game):
                original_position = utils.get_future_position_from_entity(network_id, self.client.game)
                await self.client.move(*original_position)

            await asyncio.sleep(0.01)

    async def _run(self):
        logging.info(f"Following player {self.username}")
        player = utils.get_entity_from_player_id(
            utils.get_player_id_from_username(self.username, self.client.game),
            list(self.client.game.entities.values())) # Get the player entity

        if player:
            await self.follow(player.network_id)
        else:
            logging.error(f"Player {self.username} not found")
```

As you can see it's quite simple to create your own actions. There are a few helper functions in the `utils` module that can help you with making your own actions.

## Docs
Docs can be found [here](https://antorum.readthedocs.io/)

## Logging
The bot uses the `logging` module to log information. You can configure the logger to log to a file or change the log level.
It can be very helpful while debugging to use the `DEBUG` log level. The `INFO` log level is the default and will provide useful information for a regular user.

```commandline
2024-04-28 00:09:26 [INFO] Connecting to antorum.game.ratwizard.dev:7667
2024-04-28 00:09:26 [INFO] Connected!
2024-04-28 00:09:26 [INFO] Sending handshake
2024-04-28 00:09:26 [INFO] Handshake accepted, 0 players online. Latest news:
Thanks for playing Antorum Isles!

Please report any bugs using the in-game bug reporting tool (Accessed via the F5 key), or to the #bug_report channel in the Discord.

- Declan (@dooskington)

2024-04-28 00:09:26 [INFO] Logging in as ******
2024-04-28 00:09:27 [INFO] Logged in as player 3
2024-04-28 00:09:27 [INFO] Loading game
2024-04-28 00:09:28 [INFO] (SYSTEM) : Welcome to Antorum!
2024-04-28 00:09:28 [INFO] Game loaded!
2024-04-28 00:09:29 [INFO] Starting forage action
2024-04-28 00:09:29 [INFO] Attempting to forage entity Skartweed (382)
2024-04-28 00:09:37 [INFO] (SYSTEM) : You harvest some Skartweed.
2024-04-28 00:09:37 [INFO] +9 HERBOLOGY experience (648282)
2024-04-28 00:09:37 [INFO] Adding 1 Skartweed to inventory (index 0)
2024-04-28 00:09:37 [INFO] Successfully foraged entity Skartweed (382)
2024-04-28 00:09:38 [INFO] Attempting to forage entity Skartweed (735)
```

## Contributing
As of now, we do not support all packet types that the game has.
You can add one by creating a new file in the `packets` directory and subclassing `Packet`. I recommend looking at the different packet types in the game's source code to see how they work.
This new packet type will automatically be detected by the bot and used when the game sends that packet type.
