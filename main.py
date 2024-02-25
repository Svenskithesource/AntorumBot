from antorum import multiplayer, actions
import asyncio
import logging

import secrets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


async def main():
    client = multiplayer.Client()

    await client.connect()

    await client.login(secrets.USERNAME, secrets.PASSWORD)

    while not client.logged_in:
        await asyncio.sleep(0.1)

    await client.load_game()

    await asyncio.sleep(1)
    print(client.game.local_player)
    print(client.game.local_player.inventory)
    print(client.game.resources)

    while True:
        forage = actions.ForageWeeds(client)
        await forage.run()

        await forage.wait_to_finish()

        sell = actions.SellInventory(client, "skartweed")
        await sell.run()

        await sell.wait_to_finish()

    # follow = actions.FollowPlayer(client, "Dooskington")
    # await follow.run()

    # sell = actions.SellInventory(client, "skartweed", 1)
    # await sell.run()
    #
    # while not sell.done:
    #     await asyncio.sleep(0.1)
    #
    # print(sell.result)
    # print(client.game.local_player.inventory)

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
    main_loop.run_forever()
