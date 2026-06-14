"""Deterministic schedule-based movement over configured routes."""

import random

from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.time import SimulationTime, TimeOfDayLabel
from app.domain.world import World


class MobilityEngine:
    """Move agents one route hop toward a time-of-day destination."""

    SOCIAL_DESTINATIONS = ("market", "plaza")

    def step(
        self,
        agents: list[Agent],
        world: World,
        simulation_time: SimulationTime,
        rng: random.Random,
    ) -> int:
        """Apply deterministic seeded schedule choices and return move count."""

        moved = 0
        for agent in agents:
            if agent.state == EpidemiologicalState.ISOLATED:
                agent.current_intended_destination = agent.zone_id
                continue
            destination = self._destination(agent, world, simulation_time, rng)
            agent.current_intended_destination = destination
            if destination == agent.zone_id:
                continue
            next_hop = world.next_hop(agent.zone_id, destination)
            if next_hop is None or next_hop == agent.zone_id:
                continue
            agent.zone_id = next_hop
            agent.last_moved_tick = simulation_time.tick
            moved += 1
        return moved

    def _destination(
        self,
        agent: Agent,
        world: World,
        simulation_time: SimulationTime,
        rng: random.Random,
    ) -> str:
        label = simulation_time.time_of_day_label
        routine_destination = agent.school_zone_id or agent.work_zone_id or agent.home_zone_id

        if label in {TimeOfDayLabel.NIGHT, TimeOfDayLabel.EVENING_COMMUTE}:
            return agent.home_zone_id
        if label in {
            TimeOfDayLabel.MORNING_COMMUTE,
            TimeOfDayLabel.WORK_SCHOOL,
            TimeOfDayLabel.AFTERNOON,
        }:
            return routine_destination
        if label == TimeOfDayLabel.LUNCH:
            if rng.random() < 0.35 * agent.movement_tendency:
                return self._available_social_destination(world, rng)
            return routine_destination
        if label == TimeOfDayLabel.NIGHT_SOCIAL:
            social_probability = 0.05 if agent.routine_type in {
                RoutineType.ELDERLY,
                RoutineType.REMOTE,
            } else 0.18
            if rng.random() < social_probability * agent.movement_tendency:
                return self._available_social_destination(world, rng)
            return agent.home_zone_id
        return agent.home_zone_id

    def _available_social_destination(self, world: World, rng: random.Random) -> str:
        candidates = [zone_id for zone_id in self.SOCIAL_DESTINATIONS if zone_id in world.zones]
        return rng.choice(candidates) if candidates else next(iter(world.zones))
