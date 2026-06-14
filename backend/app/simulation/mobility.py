"""Agent movement engine boundary."""

import random

from app.domain.agent import Agent
from app.domain.agent import EpidemiologicalState
from app.domain.world import World


class MobilityEngine:
    """Move a small share of agents along configured directed routes."""

    def __init__(self, move_probability: float = 0.04) -> None:
        self.move_probability = move_probability

    def step(self, agents: list[Agent], world: World, rng: random.Random) -> int:
        """Move agents in place and return how many changed zones.

        The probability is scaled by the current zone's movement weight.
        Isolated agents never move. Route selection uses configured weights.
        """

        moved = 0
        for agent in agents:
            if agent.state == EpidemiologicalState.ISOLATED:
                continue
            zone = world.zones[agent.zone_id]
            probability = min(0.25, self.move_probability * zone.movement_weight)
            if rng.random() >= probability:
                continue
            routes = world.destinations_from(agent.zone_id)
            if not routes:
                continue
            route = rng.choices(routes, weights=[item.travel_weight for item in routes], k=1)[0]
            agent.zone_id = route.destination_zone_id
            moved += 1
        return moved
