import asyncio
import datetime
import logging
import random
from typing import Dict

import multiplayer
import packets
from packets.world_entities import Entity, InteractionType
from utils import StateType, get_future_position_from_entity, get_inventory_diff


class Action:
    def __init__(self, client: multiplayer.Client):
        self.client = client
        self.is_running = False

    async def _run(self):
        # Has to be implemented by the subclass
        pass

    async def run(self):
        self.is_running = True
        task = asyncio.create_task(self._run())
        while self.is_running:
            await asyncio.sleep(0.01)

        task.cancel()

    async def stop(self):
        self.is_running = False


class ForageWeeds(Action):
    forage_coords = [(43, 247), (69, 278)]
    moving_to_coords = False

    old_inv = {}

    async def _run(self):
        logging.info("Starting forage action")

        while True:
            await asyncio.sleep(0.01)

            weed_network_id = await self.get_forageable(self.client.game.entities)

            if not weed_network_id and not self.moving_to_coords:
                weed_coords = random.choice(self.forage_coords)
                await self.client.move(weed_coords[0], weed_coords[1])
                self.moving_to_coords = True
                logging.info(f"Moving to coords {weed_coords} to forage")

                continue

            self.old_inv = self.client.game.local_player.inventory
            self.client.send_queue.put_nowait(packets.Interact(weed_network_id, InteractionType.FORAGE))
            logging.info(f"Attempting to forage entity {weed_network_id}")

            success = False
            i = 0
            while get_future_position_from_entity(self.client.game.network_id, self.client.game) != \
                    self.client.game.entities[weed_network_id].states[StateType.TRANSFORM].state.position:
                await asyncio.sleep(0.1)

                i += 1
                if i > 50:
                    logging.warning(f"Failed to trigger forage on entity {weed_network_id} after 5 seconds")
                    break
            else:
                success = True

            if not success:
                self.moving_to_coords = False
                continue

            success = False
            i = 0
            while not get_inventory_diff(self.old_inv, self.client.game.local_player.inventory):
                await asyncio.sleep(0.1)

                i += 1
                if i > 200:
                    logging.warning(f"Foraging still didn't happen after 20 seconds, continuing")
                    break
            else:
                success = True

            self.moving_to_coords = False

            if not success:
                continue

            logging.info(f"Successfully foraged entity {weed_network_id}")

    async def get_forageable(self, entities: Dict[int, Entity]):
        for entity in entities.values():
            if InteractionType.FORAGE in entity.states[StateType.INTERACTABLE].state.interactions:
                return entity.network_id
