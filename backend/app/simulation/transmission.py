"""Disease progression and local stochastic transmission."""

import math
import random
from dataclasses import dataclass, field
from statistics import fmean

from app.domain.agent import Agent, EpidemiologicalState
from app.domain.disease import DiseaseProfile
from app.domain.world import World
from app.simulation.contacts import ContactBatch
from app.simulation.policies import PolicyModifiers

# Strength of agent behavior on the per-tick infection hazard (Phase 5).
_SUSCEPTIBLE_PROTECTION_STRENGTH = 0.6
_INFECTIOUS_PROTECTION_STRENGTH = 0.5
_DISTANCING_STRENGTH = 0.35
_RISK_COMPENSATION_STRENGTH = 0.6


@dataclass(frozen=True, slots=True)
class TransmissionResult:
    """Infections produced this tick plus behavior-on-transmission aggregates."""

    infections_by_zone: dict[str, int] = field(default_factory=dict)
    effective_beta_mean: float = 0.0
    behavioral_transmission_reduction: float = 0.0
    misinformation_transmission_amplification: float = 0.0


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
    ) -> TransmissionResult:
        """Apply the prevalence hazard, modulated by policy and agent behavior.

        Protective behavior (susceptible protection, infectious protection and
        distancing) lowers the hazard; risk compensation from believed safety or
        fatigue raises it. Returns infections per zone plus transparent aggregates
        of how behavior shifted the effective transmission coefficient.
        """

        modifiers = policy_modifiers or PolicyModifiers()
        infections_by_zone: dict[str, int] = {}
        tick_fraction = disease.tick_minutes / 1440
        sum_policy = 0.0
        sum_protective = 0.0
        sum_full = 0.0
        for context in contact_batch.contexts.values():
            if context.infectious_pressure == 0:
                infections_by_zone[context.zone_id] = 0
                continue
            zone = world.zones[context.zone_id]
            infectious_prevalence = context.infectious_pressure / len(context.agents)
            density_modifier = 0.5 + min(1.5, len(context.agents) / zone.capacity)
            policy_hazard = (
                disease.beta_base
                * tick_fraction
                * zone.contact_rate
                * density_modifier
                * infectious_prevalence
                * modifiers.contact_multiplier(context.zone_id)
                * modifiers.transmission_multiplier(context.zone_id)
            )
            protective_factor, amplifying_factor = self._behavior_factors(context.agents)
            behavior_factor = protective_factor * amplifying_factor
            probability = 1 - math.exp(-policy_hazard * behavior_factor)
            new_infections = 0
            susceptibles = 0
            for agent in context.agents:
                if agent.state == EpidemiologicalState.SUSCEPTIBLE:
                    susceptibles += 1
                    if rng.random() < probability:
                        agent.state = EpidemiologicalState.EXPOSED
                        agent.exposed_at_tick = tick
                        new_infections += 1
            infections_by_zone[context.zone_id] = new_infections
            weight = susceptibles or 1
            sum_policy += policy_hazard * weight
            sum_protective += policy_hazard * protective_factor * weight
            sum_full += policy_hazard * behavior_factor * weight

        if sum_policy > 0:
            effective_beta_mean = round(disease.beta_base * sum_full / sum_policy, 6)
            behavioral_reduction = round(max(0.0, 1 - sum_protective / sum_policy), 6)
            misinformation_amplification = round(
                max(0.0, sum_full / sum_protective - 1) if sum_protective else 0.0, 6
            )
        else:
            effective_beta_mean = 0.0
            behavioral_reduction = 0.0
            misinformation_amplification = 0.0

        return TransmissionResult(
            infections_by_zone=infections_by_zone,
            effective_beta_mean=effective_beta_mean,
            behavioral_transmission_reduction=behavioral_reduction,
            misinformation_transmission_amplification=misinformation_amplification,
        )

    @staticmethod
    def _behavior_factors(agents: list[Agent]) -> tuple[float, float]:
        """Return (protective_factor, amplifying_factor) for one zone."""

        susceptible_protection = [
            agent.protection_behavior
            for agent in agents
            if agent.state == EpidemiologicalState.SUSCEPTIBLE
        ]
        outgoing_protection = [
            max(agent.protection_behavior, agent.distancing_behavior)
            for agent in agents
            if agent.is_infectious
        ]
        mean_sus = fmean(susceptible_protection) if susceptible_protection else 0.0
        mean_out = fmean(outgoing_protection) if outgoing_protection else 0.0
        mean_distancing = fmean(agent.distancing_behavior for agent in agents)
        mean_risk_comp = fmean(agent.risk_compensation for agent in agents)
        protective_factor = (
            (1 - mean_sus * _SUSCEPTIBLE_PROTECTION_STRENGTH)
            * (1 - mean_out * _INFECTIOUS_PROTECTION_STRENGTH)
            * (1 - mean_distancing * _DISTANCING_STRENGTH)
        )
        amplifying_factor = 1 + mean_risk_comp * _RISK_COMPENSATION_STRENGTH
        return max(0.0, protective_factor), amplifying_factor
