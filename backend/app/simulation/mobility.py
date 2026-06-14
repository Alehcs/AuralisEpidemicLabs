"""Deterministic schedule-based movement over configured routes."""

import random
from dataclasses import dataclass

from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.time import SimulationTime, TimeOfDayLabel
from app.domain.world import World
from app.simulation.policies import PolicyModifiers


@dataclass(frozen=True, slots=True, eq=False)
class MobilityResult:
    """Observed movement and estimated movements prevented by policy."""

    moved: int = 0
    attempted: int = 0
    policy_blocked: int = 0

    def __int__(self) -> int:
        return self.moved

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            return self.moved == other
        if isinstance(other, MobilityResult):
            return (
                self.moved,
                self.attempted,
                self.policy_blocked,
            ) == (
                other.moved,
                other.attempted,
                other.policy_blocked,
            )
        return NotImplemented


class MobilityEngine:
    """Move agents one route hop toward a time-of-day destination."""

    SOCIAL_DESTINATIONS = ("market", "plaza")

    def step(
        self,
        agents: list[Agent],
        world: World,
        simulation_time: SimulationTime,
        rng: random.Random,
        policy_modifiers: PolicyModifiers | None = None,
    ) -> MobilityResult:
        """Apply deterministic seeded schedule choices and return move count."""

        modifiers = policy_modifiers or PolicyModifiers()
        moved = 0
        attempted = 0
        policy_blocked = 0
        for agent in agents:
            if agent.state == EpidemiologicalState.ISOLATED:
                agent.current_intended_destination = agent.zone_id
                continue
            destination, optional = self._destination(agent, world, simulation_time, rng)
            agent.current_intended_destination = destination
            if destination == agent.zone_id:
                continue
            attempted += 1
            next_hop = world.next_hop(agent.zone_id, destination)
            if next_hop is None or next_hop == agent.zone_id:
                continue
            multiplier = min(
                modifiers.mobility_multiplier(agent.zone_id),
                modifiers.mobility_multiplier(next_hop),
                modifiers.mobility_multiplier(destination),
            )
            if destination in modifiers.closed_zones:
                multiplier = min(multiplier, 0.05)
            if not optional:
                multiplier = 1 - (1 - multiplier) * 0.35
            compliance_effect = 1 - (1 - multiplier) * agent.adaptive_compliance
            if rng.random() > compliance_effect:
                policy_blocked += 1
                continue
            agent.zone_id = next_hop
            agent.last_moved_tick = simulation_time.tick
            moved += 1
        return MobilityResult(moved=moved, attempted=attempted, policy_blocked=policy_blocked)

    def _destination(
        self,
        agent: Agent,
        world: World,
        simulation_time: SimulationTime,
        rng: random.Random,
    ) -> tuple[str, bool]:
        label = simulation_time.time_of_day_label
        routine_destination = agent.school_zone_id or agent.work_zone_id or agent.home_zone_id

        if label in {TimeOfDayLabel.NIGHT, TimeOfDayLabel.EVENING_COMMUTE}:
            return agent.home_zone_id, False
        if label in {
            TimeOfDayLabel.MORNING_COMMUTE,
            TimeOfDayLabel.WORK_SCHOOL,
            TimeOfDayLabel.AFTERNOON,
        }:
            return routine_destination, False
        if label == TimeOfDayLabel.LUNCH:
            if rng.random() < 0.35 * agent.movement_tendency * self._social_drive(agent):
                return self._available_social_destination(world, rng), True
            return routine_destination, False
        if label == TimeOfDayLabel.NIGHT_SOCIAL:
            social_probability = 0.05 if agent.routine_type in {
                RoutineType.ELDERLY,
                RoutineType.REMOTE,
            } else 0.18
            drive = social_probability * agent.movement_tendency * self._social_drive(agent)
            if rng.random() < drive:
                return self._available_social_destination(world, rng), True
            return agent.home_zone_id, False
        return agent.home_zone_id, False

    @staticmethod
    def _social_drive(agent: Agent) -> float:
        """Behavior multiplier on optional/social trips only.

        Distancing behavior suppresses voluntary outings; the risky optional
        movement bias (curiosity, fatigue-driven restriction breaking, believed
        safety) pushes agents back out. Mandatory work/school movement does not
        use this multiplier, so essential trips stay comparatively stable.
        """

        drive = (1.0 - 0.6 * agent.distancing_behavior) * (
            1.0 + 0.6 * agent.risky_optional_movement_bias
        )
        return max(0.0, min(1.6, drive))

    def _available_social_destination(self, world: World, rng: random.Random) -> str:
        candidates = [zone_id for zone_id in self.SOCIAL_DESTINATIONS if zone_id in world.zones]
        return rng.choice(candidates) if candidates else next(iter(world.zones))
