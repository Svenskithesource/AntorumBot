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
    get_nearest_entity, time_to_dest, coords_in_bounds


class Action:
    def __init__(self, client: multiplayer.Client):
        self.client = client
        self._task: asyncio.Task = None

    async def run_wrapper(self):
        try:
            await self._run()
        except Exception as e:
            traceback.print_exception(
                type(e), e, e.__traceback__
            )

    async def _run(self):
        # Has to be implemented by the subclass
        pass

    async def run(self):
        self._task = asyncio.create_task(self.run_wrapper())

    def stop(self):
        logging.info(f"Stopping action {self.__class__.__name__}")
        self._task.cancel()


class ForageWeeds(Action):
    forage_coords = map_to_game_coords([(21, 5573), (547, 4600), (390, 5082)])

    old_inv = {}

    async def _run(self):
        logging.info("Starting forage action")
        if not coords_in_bounds(self.client.game.local_player.position, self.forage_coords[:2]):
            logging.info("Moving to forage area")
            await self.client.move(self.forage_coords[2][0], self.forage_coords[2][1])

        while True:
            await asyncio.sleep(0.1)

            weed = await self.get_nearest_forageable(self.client.game.entities)

            if not weed:
                await asyncio.sleep(1)
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
                                       movement.speed) + 10  # 10 seconds for good measure
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
            if InteractionType.FORAGE in entity.states[StateType.INTERACTABLE].state.interactions and coords_in_bounds(
                    entity.states[StateType.TRANSFORM].state.position, self.forage_coords):
                forageables[entity.network_id] = entity

        return get_nearest_entity(self.client.game.local_player.position, forageables)


class FollowPlayer(Action):
    def __init__(self, client: "multiplayer.Client", username: str):
        super().__init__(client)
        self.username = username

    async def follow(self, network_id: int):
        logging.debug(f"Following entity {network_id}")
        original_position = utils.get_future_position_from_entity(network_id, self.client.game)

        if original_position != self.client.game.local_player.position:
            await self.client.move(*original_position)

        while True:
            if original_position != utils.get_future_position_from_entity(network_id, self.client.game):
                original_position = utils.get_future_position_from_entity(network_id, self.client.game)
                await self.client.move(original_position[0], original_position[1])

            await asyncio.sleep(0.01)

    async def _run(self):
        try:
            logging.info(f"Following player {self.username}")
            network_id = utils.get_entity_from_player_id(
                utils.get_player_id_from_username(self.username, self.client.game),
                list(self.client.game.entities.values())).network_id

            if network_id:
                await self.follow(network_id)
            else:
                logging.error(f"Player {self.username} not found")
        except Exception as e:
            traceback.print_exception(
                type(e), e, e.__traceback__
            )
