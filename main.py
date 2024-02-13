import multiplayer
import asyncio
import logging

import secrets
import state

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


async def main():
    client = multiplayer.Client()

    asyncio.create_task(client.update())
    await client.connect()

    await asyncio.sleep(1)

    await client.login(secrets.USERNAME, secrets.PASSWORD)

    while not state.logged_in:
        await asyncio.sleep(0.1)


asyncio.run(main())  # Execute within the asyncio event loop
