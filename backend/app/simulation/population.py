"""Deterministic population creation from validated configs."""

import random

from app.domain.agent import Agent, EpidemiologicalState
from app.domain.disease import DiseaseProfile
from app.domain.world import World
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig


class PopulationGenerator:
    """Create agents, assign profiles/zones, and seed the initial outbreak."""

    def generate(
        self,
        config: AgentPopulationConfig,
        world: World,
        disease: DiseaseProfile,
        outbreak: InitialOutbreakConfig,
        seed: int,
    ) -> list[Agent]:
        """Return the same initial population for identical inputs and seed."""

        rng = random.Random(seed)
        zones = list(world.zones.values())
        profiles = [profile.profile for profile in config.profiles]
        profile_weights = [profile.proportion for profile in config.profiles]
        zone_weights = [zone.capacity for zone in zones]

        agents = [
            Agent(
                id=f"agent-{index:05d}",
                profile=rng.choices(profiles, weights=profile_weights, k=1)[0],
                zone_id=rng.choices(zones, weights=zone_weights, k=1)[0].id,
            )
            for index in range(config.population_size)
        ]

        outbreak_candidates = [agent for agent in agents if agent.zone_id == outbreak.zone_id]
        seed_count = outbreak.exposed_agents + outbreak.infected_agents
        if len(outbreak_candidates) < seed_count:
            raise ValueError(
                f"Outbreak zone '{outbreak.zone_id}' has {len(outbreak_candidates)} agents "
                f"but {seed_count} seeds were requested"
            )
        seeded_agents = rng.sample(outbreak_candidates, seed_count)

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
