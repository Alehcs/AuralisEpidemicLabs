"""Disease exposure and progression engine boundary."""

import math
import random

from app.domain.agent import Agent
from app.domain.agent import EpidemiologicalState
from app.domain.disease import DiseaseProfile
from app.domain.world import World
from app.simulation.contacts import ContactEngine


class TransmissionEngine:
    """Apply disease progression and aggregate zone-level transmission."""

    def __init__(self, contact_engine: ContactEngine | None = None) -> None:
        self.contact_engine = contact_engine or ContactEngine()

    def step(
        self,
        agents: list[Agent],
        world: World,
        disease: DiseaseProfile,
        tick: int,
        rng: random.Random,
    ) -> int:
        """Advance disease state and return newly exposed agent count.

        Susceptible infection probability in a zone is ``1 - exp(-hazard)``.
        Hazard is beta per contact multiplied by effective contacts per day,
        tick fraction, infectious prevalence, and bounded zone density. This
        avoids an O(n^2) loop while preserving local agent stochasticity.
        """

        self._progress_existing_infections(agents, disease, tick, rng)

        new_infections = 0
        tick_fraction = disease.tick_minutes / 1440
        for context in self.contact_engine.step(agents).values():
            if context.infectious_pressure == 0:
                continue
            zone = world.zones[context.zone_id]
            infectious_prevalence = context.infectious_pressure / len(context.agents)
            density_modifier = 0.5 + min(1.5, len(context.agents) / zone.capacity)
            hazard = (
                disease.beta_base
                * tick_fraction
                * zone.contact_rate
                * density_modifier
                * infectious_prevalence
            )
            infection_probability = 1 - math.exp(-hazard)
            for agent in context.agents:
                if agent.state != EpidemiologicalState.SUSCEPTIBLE:
                    continue
                if rng.random() < infection_probability:
                    agent.state = EpidemiologicalState.EXPOSED
                    agent.exposed_at_tick = tick
                    new_infections += 1

        return new_infections

    @staticmethod
    def _progress_existing_infections(
        agents: list[Agent],
        disease: DiseaseProfile,
        tick: int,
        rng: random.Random,
    ) -> None:
        for agent in agents:
            if (
                agent.state == EpidemiologicalState.EXPOSED
                and agent.exposed_at_tick is not None
                and tick - agent.exposed_at_tick >= disease.incubation_ticks
            ):
                asymptomatic = rng.random() < disease.asymptomatic_probability
                agent.state = (
                    EpidemiologicalState.INFECTED_ASYMPTOMATIC
                    if asymptomatic
                    else EpidemiologicalState.INFECTED_SYMPTOMATIC
                )
                agent.infected_at_tick = tick
                agent.infectiousness = 0.65 if asymptomatic else 1.0
            elif (
                agent.is_infectious
                and agent.infected_at_tick is not None
                and tick - agent.infected_at_tick >= disease.infectious_ticks
            ):
                agent.state = EpidemiologicalState.RECOVERED
                agent.recovered_at_tick = tick
                agent.infectiousness = 0.0
