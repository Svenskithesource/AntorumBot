import asyncio
import copy
import logging
import random
import traceback
from typing import Dict

import multiplayer
import packets
import utils
from packets.world_entities import Entity, InteractionType
from utils import StateType, get_future_position_from_entity, get_inventory_diff, map_to_game_coords, is_nearby, \
    get_nearest_safe_entity, time_to_dest


class Action:
    def __init__(self, client: multiplayer.Client):
        self.client = client
        self.is_running = False

    async def _run(self):
        # Has to be implemented by the subclass
        pass

    async def run(self):
        self.is_running = True
        task = asyncio.get_running_loop().create_task(self._run())
        while self.is_running:
            await asyncio.sleep(0.01)

            try:
                if exception := task.exception():
                    traceback.print_exception(
                        type(exception), exception, exception.__traceback__
                    )
                    break
            except asyncio.InvalidStateError:
                continue

        task.cancel()

    async def stop(self):
        self.is_running = False


class ForageWeeds(Action):
    forage_coords = map_to_game_coords([(364, 5075)])  # (540, 3960)
    moving_to_coords = False

    old_inv = {}

    async def _run(self):
        logging.info("Starting forage action")

        while True:
            await asyncio.sleep(1)

            weed = await self.get_nearest_forageable(self.client.game.entities)

            if not weed and not self.moving_to_coords:
                weed_coords = random.choice(self.forage_coords)
                await self.client.move(weed_coords[0], weed_coords[1])
                self.moving_to_coords = True
                logging.info(f"Moving to coords {weed_coords} to forage")

                continue
            elif not weed:
                continue

            self.old_inv = copy.deepcopy(self.client.game.local_player.inventory)
            self.client.send_queue.put_nowait(packets.Interact(weed.network_id, InteractionType.FORAGE))
            logging.info(f"Attempting to forage entity {weed.states[StateType.INFO].state.name} ({weed.network_id})")

            success = False
            i = 0
            while is_nearby(get_future_position_from_entity(self.client.game.network_id, self.client.game),
                            self.client.game.entities[weed.network_id].states[StateType.TRANSFORM].state.position, 2):
                await asyncio.sleep(0.1)

                i += 1
                if i > 50:
                    logging.warning(
                        f"Failed to trigger forage on entity {weed.states[StateType.INFO].state.name} ({weed.network_id}) after 5 seconds")
                    break
            else:
                success = True

            if not success:
                self.moving_to_coords = False
                continue

            success = False
            i = 0
            movement = self.client.game.entities[self.client.game.network_id].states[StateType.MOVEMENT].state

            travel_time = time_to_dest(self.client.game.local_player.position, movement.destinations,
                                       movement.speed) + 2  # 2 seconds for good measure
            logging.debug(f"Travel time to forage: {travel_time} seconds")

            while not get_inventory_diff(self.old_inv, self.client.game.local_player.inventory)[0]:
                await asyncio.sleep(0.1)

                i += 1
                if i > travel_time * 10:
                    logging.warning(f"Foraging still didn't happen after {travel_time} seconds, continuing")
                    break
            else:
                success = True

            self.moving_to_coords = False

            if not success:
                continue

            logging.info(f"Successfully foraged entity {weed.states[StateType.INFO].state.name} ({weed.network_id})")

    async def get_nearest_forageable(self, entities: Dict[int, Entity]) -> Entity:
        forageables = {}

        for entity in entities.values():
            if InteractionType.FORAGE in entity.states[StateType.INTERACTABLE].state.interactions:
                forageables[entity.network_id] = entity

        return get_nearest_safe_entity(self.client.game.local_player.position, forageables, entities)
