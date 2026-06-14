"""Disease progression and local stochastic transmission."""

import math
import random

from app.domain.agent import Agent, EpidemiologicalState
from app.domain.disease import DiseaseProfile
from app.domain.world import World
from app.simulation.contacts import ContactBatch
from app.simulation.policies import PolicyModifiers


class TransmissionEngine:
    """Progress disease states and expose susceptible agents by zone."""

    def progress(
        self,
        agents: list[Agent],
        disease: DiseaseProfile,
        tick: int,
        rng: random.Random,
    ) -> None:
        """Advance exposed/infected agents before contacts are generated."""

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

    def transmit(
        self,
        contact_batch: ContactBatch,
        world: World,
        disease: DiseaseProfile,
        tick: int,
        rng: random.Random,
        policy_modifiers: PolicyModifiers | None = None,
    ) -> dict[str, int]:
        """Apply the Phase 1 prevalence hazard and return infections by zone."""

        modifiers = policy_modifiers or PolicyModifiers()
        infections_by_zone: dict[str, int] = {}
        tick_fraction = disease.tick_minutes / 1440
        for context in contact_batch.contexts.values():
            if context.infectious_pressure == 0:
                infections_by_zone[context.zone_id] = 0
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
                * modifiers.contact_multiplier(context.zone_id)
                * modifiers.transmission_multiplier(context.zone_id)
            )
            probability = 1 - math.exp(-hazard)
            new_infections = 0
            for agent in context.agents:
                if agent.state == EpidemiologicalState.SUSCEPTIBLE and rng.random() < probability:
                    agent.state = EpidemiologicalState.EXPOSED
                    agent.exposed_at_tick = tick
                    new_infections += 1
            infections_by_zone[context.zone_id] = new_infections
        return infections_by_zone
