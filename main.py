import multiplayer
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


async def main():
    client = multiplayer.Client()
    await client.connect()

    while True:
        await client.update()
        await asyncio.sleep(0.1)


asyncio.run(main())  # Execute within the asyncio event loop
