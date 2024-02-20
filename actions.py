import asyncio
import copy
import datetime
import logging
import random
import traceback
from typing import Dict, List

import multiplayer
import packets
import utils
from packets.barter_close import BarterStatus
from packets.barter_open import BarterInventoryItemArea
from packets.world_entities import Entity, InteractionType
from utils import StateType, get_future_position_from_entity, message_contains_since, map_to_game_coords, is_nearby, \
    get_nearest_entity, time_to_dest, coords_in_bounds, inventory_contains_resource_id, wait_for, get_resource_by_name, \
    get_inventory_slot_by_resource_id, amount_of_resource_in_inventory


class Action:
    def __init__(self, client: multiplayer.Client):
        self.client = client
        self._task: asyncio.Task = None

    @property
    def done(self):
        return self._task.done()

    @property
    def result(self):
        try:
            return self._task.result()
        except (asyncio.CancelledError, asyncio.InvalidStateError):
            return None

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
    last_weed_id = 0

    async def _run(self):
        logging.info("Starting forage action")
        if not coords_in_bounds(self.client.game.local_player.position, self.forage_coords[:2]):
            logging.info("Moving to forage area")
            await self.client.move(self.forage_coords[2][0], self.forage_coords[2][1])

        while True:
            await asyncio.sleep(0.1)

            weed = await self.get_nearest_forageable(self.client.game.entities, [self.last_weed_id])

            if not weed:
                await asyncio.sleep(1)
                continue

            self.client.send_queue.put_nowait(packets.Interact(weed.network_id, InteractionType.FORAGE))
            logging.info(f"Attempting to forage entity {weed.states[StateType.INFO].state.name} ({weed.network_id})")

            success = await wait_for(
                lambda: is_nearby(get_future_position_from_entity(self.client.game.network_id, self.client.game),
                                  self.client.game.entities[weed.network_id].states[
                                      StateType.TRANSFORM].state.position, 5), 5)

            if not success:
                logging.warning(
                    f"Failed to trigger forage on entity {weed.states[StateType.INFO].state.name} ({weed.network_id}) after 5 seconds")
                self.moving_to_coords = False
                continue

            movement = self.client.game.entities[self.client.game.network_id].states[StateType.MOVEMENT].state
            start_time = datetime.datetime.now()
            travel_time = time_to_dest(self.client.game.local_player.position, movement.destinations,
                                       movement.speed) + 10  # 10 seconds for good measure
            self.last_weed_id = weed.network_id

            logging.debug(f"Travel time to forage: {travel_time} seconds")

            success = await wait_for(
                lambda: message_contains_since("You harvest", self.client.game.chat_log, start_time), travel_time)

            self.moving_to_coords = False

            if not success:
                continue

            logging.info(f"Successfully foraged entity {weed.states[StateType.INFO].state.name} ({weed.network_id})")

    async def get_nearest_forageable(self, entities: Dict[int, Entity], excluded: List[int]) -> Entity:
        forageables = {}

        for entity in entities.values():
            if InteractionType.FORAGE in entity.states[StateType.INTERACTABLE].state.interactions and coords_in_bounds(
                    entity.states[StateType.TRANSFORM].state.position,
                    self.forage_coords) and entity.network_id not in excluded:
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
        logging.info(f"Following player {self.username}")
        player = utils.get_entity_from_player_id(
            utils.get_player_id_from_username(self.username, self.client.game),
            list(self.client.game.entities.values()))

        if player:
            await self.follow(player.network_id)
        else:
            logging.error(f"Player {self.username} not found")


class SellInventory(Action):
    barter_coords = map_to_game_coords([(355, 3567)])
    is_moving = False

    def __init__(self, client: "multiplayer.Client", item_name: str, amount: int = 0):
        super().__init__(client)
        self.item_name = item_name
        self.item = get_resource_by_name(item_name, self.client.game.resources)

        if not self.item:
            logging.error(f"Item {item_name} not found")
            return

        if amount == 0:
            self.amount = amount_of_resource_in_inventory(self.item.resource_id,
                                                          self.client.game.local_player.inventory)
        else:
            self.amount = amount

    async def _run(self):
        logging.info(f"Selling {self.amount} {self.item_name}")

        if not inventory_contains_resource_id(self.item.resource_id, self.client.game.local_player.inventory,
                                              self.amount):
            logging.error(f"Not enough of item {self.item_name} to sell")
            return

        while not (barter := (await self.get_barter_entity(self.client.game.entities))):
            await asyncio.sleep(0.5)
            if not self.is_moving:
                await self.client.move(self.barter_coords[0][0], self.barter_coords[0][1])

        self.is_moving = False

        self.client.send_queue.put_nowait(packets.Interact(barter.network_id, InteractionType.BARTER))

        logging.info(f"Attempting to barter with entity {barter.network_id}")

        success = await wait_for(
            lambda: is_nearby(get_future_position_from_entity(self.client.game.network_id, self.client.game),
                              self.client.game.entities[barter.network_id].states[
                                  StateType.TRANSFORM].state.position, 5), 5)

        if not success:
            logging.warning(
                f"Failed to trigger barter on entity {barter.states[StateType.INFO].state.name} ({barter.network_id}) after 5 seconds")
            return False

        travel_time = time_to_dest(self.client.game.local_player.position,
                                   self.client.game.entities[barter.network_id].states[
                                       StateType.MOVEMENT].state.destinations,
                                   self.client.game.entities[self.client.game.network_id].states[
                                       StateType.MOVEMENT].state.speed) + 10

        success = await wait_for(lambda: self.client.game.barter, travel_time)

        if not success:
            logging.warning(f"Failed to open barter after {travel_time} seconds")
            return False

        slot = get_inventory_slot_by_resource_id(self.item.resource_id, self.client.game.local_player.inventory)

        self.client.send_queue.put_nowait(packets.BarterMove(BarterInventoryItemArea.INVENTORY, slot, self.amount))

        success = await wait_for(lambda: self.client.game.barter.you_offer, 5)

        if not success:
            logging.warning(f"Failed to move item to barter after 5 seconds")
            self.client.send_queue.put_nowait(packets.BarterClose(BarterStatus.DECLINED))
            return False

        self.client.send_queue.put_nowait(packets.BarterClose(BarterStatus.ACCEPTED))

        success = await wait_for(lambda: not self.client.game.barter, 5)

        if not success:
            logging.warning(f"Failed to close barter after 5 seconds")
            return False

        return True

    async def get_barter_entity(self, entities: Dict[int, Entity]):
        barters = {}

        for entity in entities.values():
            if InteractionType.BARTER in entity.states[StateType.INTERACTABLE].state.interactions:
                barters[entity.network_id] = entity

        return get_nearest_entity(self.client.game.local_player.position, barters)
