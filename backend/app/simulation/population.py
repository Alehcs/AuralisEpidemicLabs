"""Deterministic population creation and schedule assignment."""

import random

from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.disease import DiseaseProfile
from app.domain.world import World, Zone
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig


class PopulationGenerator:
    """Create agents, assign stable routines/zones, and seed an outbreak."""

    def generate(
        self,
        config: AgentPopulationConfig,
        world: World,
        disease: DiseaseProfile,
        outbreak: InitialOutbreakConfig,
        seed: int,
    ) -> list[Agent]:
        """Return identical schedule assignments for identical inputs and seed."""

        rng = random.Random(seed)
        zones = list(world.zones.values())
        home_zones = self._zones_by_kind(zones, {"residential", "periphery"}) or zones
        profiles = [profile.profile for profile in config.profiles]
        profile_weights = [profile.proportion for profile in config.profiles]
        routines = [RoutineType(item.routine_type) for item in config.routines]
        routine_weights = [item.proportion for item in config.routines]

        agents = []
        for index in range(config.population_size):
            routine = rng.choices(routines, weights=routine_weights, k=1)[0]
            home = rng.choices(home_zones, weights=[zone.capacity for zone in home_zones], k=1)[0]
            work_zone_id, school_zone_id = self._assignment_for_routine(routine, world, rng)
            agents.append(
                Agent(
                    id=f"agent-{index:05d}",
                    profile=rng.choices(profiles, weights=profile_weights, k=1)[0],
                    zone_id=home.id,
                    home_zone_id=home.id,
                    work_zone_id=work_zone_id,
                    school_zone_id=school_zone_id,
                    routine_type=routine,
                    movement_tendency=round(rng.uniform(0.55, 1.0), 6),
                    compliance_tendency=round(rng.uniform(0.2, 0.95), 6),
                    isolation_compliance=round(rng.uniform(0.2, 0.95), 6),
                )
            )

        seed_count = outbreak.exposed_agents + outbreak.infected_agents
        seeded_agents = rng.sample(agents, seed_count)
        for agent in seeded_agents:
            agent.zone_id = outbreak.zone_id
            agent.current_intended_destination = outbreak.zone_id

        for agent in seeded_agents[: outbreak.exposed_agents]:
            agent.state = EpidemiologicalState.EXPOSED
            agent.exposed_at_tick = 0

        for agent in seeded_agents[outbreak.exposed_agents :]:
            asymptomatic = rng.random() < disease.asymptomatic_probability
            agent.state = (
                EpidemiologicalState.INFECTED_ASYMPTOMATIC
                if asymptomatic
                else EpidemiologicalState.INFECTED_SYMPTOMATIC
            )
            agent.exposed_at_tick = 0
            agent.infected_at_tick = 0
            agent.infectiousness = 0.65 if asymptomatic else 1.0
        return agents

    @staticmethod
    def _zones_by_kind(zones: list[Zone], kinds: set[str]) -> list[Zone]:
        return [zone for zone in zones if zone.kind in kinds]

    def _assignment_for_routine(
        self,
        routine: RoutineType,
        world: World,
        rng: random.Random,
    ) -> tuple[str | None, str | None]:
        zones = list(world.zones.values())
        by_kind = {zone.kind: zone.id for zone in zones}
        if routine == RoutineType.STUDENT:
            school = by_kind.get("mixed", "work_school")
            return None, school
        if routine == RoutineType.TRADER:
            return by_kind.get("commerce", "market"), None
        if routine == RoutineType.HEALTHCARE:
            return by_kind.get("healthcare", "hospital"), None
        if routine == RoutineType.WORKER:
            candidates = [
                zone.id for zone in zones if zone.kind in {"mixed", "commerce", "transport"}
            ]
            return rng.choice(candidates), None
        return None, None
