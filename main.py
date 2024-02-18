import multiplayer
import asyncio
import logging

import secrets

import actions
from utils import StateType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


async def main():
    client = multiplayer.Client()

    asyncio.get_running_loop().create_task(client.update())
    await client.connect()

    await client.login(secrets.USERNAME, secrets.PASSWORD)

    while not client.logged_in:
        await asyncio.sleep(0.1)

    await client.load_game()

    await asyncio.sleep(2)
    print(client.game.local_player)
    forage = actions.ForageWeeds(client)
    await forage.run()
    # await client.move(25, 124)
    # await client.move(50, 360)
    # asyncio.create_task(client.follow_player("IlexBOT"))
    # await client.move(240, 601)

    # while True:
    #     logging.info(f"Player {client.game.local_player}")
    #     # logging.info(f"Player stats: {client.game.local_player.stats}")
    #     logging.info(f"Player inventory: {client.game.local_player.inventory}")
    #     await asyncio.sleep(5)


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
