"""Aggregate explicit contact records without materializing all pairs."""

from collections import Counter, defaultdict
from dataclasses import dataclass

from app.domain.agent import Agent
from app.domain.behavior_params import BehaviorParameters
from app.domain.contacts import ContactRecord
from app.domain.world import World
from app.simulation.policies import PolicyModifiers


@dataclass(slots=True)
class ZoneContactContext:
    """Agents and infectious pressure currently co-located in one zone."""

    zone_id: str
    agents: list[Agent]
    infectious_pressure: float


# Risk compensation re-thickens contacts; its contact-level strength stays fixed
# while distancing strength is configurable via BehaviorParameters.
_RISK_COMPENSATION_STRENGTH = 0.5


@dataclass(slots=True)
class ContactBatch:
    """Contexts used for transmission and compact records retained for replay.

    ``raw_contact_count`` is pre-intervention mixing, ``policy_contact_count``
    applies only scheduled policy reductions, and ``effective_contact_count``
    additionally folds in emergent agent behavior (distancing vs risk
    compensation).
    """

    contexts: dict[str, ZoneContactContext]
    records: list[ContactRecord]
    raw_contact_count: int = 0
    policy_contact_count: int = 0
    effective_contact_count: int = 0


class ContactEngine:
    """Create one deterministic aggregate contact record per populated zone."""

    def step(
        self,
        agents: list[Agent],
        world: World,
        tick: int,
        tick_minutes: int,
        policy_modifiers: PolicyModifiers | None = None,
        params: BehaviorParameters | None = None,
    ) -> ContactBatch:
        modifiers = policy_modifiers or PolicyModifiers()
        params = params or BehaviorParameters()
        grouped: dict[str, list[Agent]] = defaultdict(list)
        for agent in agents:
            grouped[agent.zone_id].append(agent)

        contexts: dict[str, ZoneContactContext] = {}
        records: list[ContactRecord] = []
        raw_total = 0
        policy_total = 0
        effective_total = 0
        tick_fraction = tick_minutes / 1440
        for zone_id, local_agents in grouped.items():
            zone = world.zones[zone_id]
            counts = Counter(agent.state.value for agent in local_agents)
            infectious_pressure = sum(
                agent.infectiousness * (0.1 if agent.state.value == "isolated" else 1.0)
                for agent in local_agents
                if agent.is_infectious
            )
            population = len(local_agents)
            density = population / zone.capacity
            baseline_contacts = round(population * zone.contact_rate * tick_fraction / 2)
            contact_multiplier = modifiers.contact_multiplier(zone_id)
            behavior_multiplier = self._behavior_multiplier(local_agents, params)
            effective_multiplier = contact_multiplier * behavior_multiplier
            policy_contacts = round(baseline_contacts * contact_multiplier)
            contact_count = round(baseline_contacts * effective_multiplier)
            raw_total += baseline_contacts
            policy_total += policy_contacts
            effective_total += contact_count
            infectious_prevalence = infectious_pressure / population
            susceptible_exposed = round(
                counts["susceptible"]
                * zone.contact_rate
                * effective_multiplier
                * tick_fraction
                * infectious_prevalence
            )
            contexts[zone_id] = ZoneContactContext(
                zone_id=zone_id,
                agents=local_agents,
                infectious_pressure=infectious_pressure,
            )
            records.append(
                ContactRecord(
                    tick=tick,
                    zone_id=zone_id,
                    contact_count=contact_count,
                    susceptible_exposed_contacts=susceptible_exposed,
                    infectious_contacts=round(contact_count * infectious_prevalence),
                    new_infections=0,
                    average_zone_density=round(density, 6),
                )
            )
        return ContactBatch(
            contexts=contexts,
            records=records,
            raw_contact_count=raw_total,
            policy_contact_count=policy_total,
            effective_contact_count=effective_total,
        )

    @staticmethod
    def _behavior_multiplier(
        local_agents: list[Agent],
        params: BehaviorParameters,
    ) -> float:
        """Mean distancing thins contacts; mean risk compensation re-thickens."""

        population = len(local_agents)
        if not population:
            return 1.0
        mean_distancing = sum(agent.distancing_behavior for agent in local_agents) / population
        mean_risk_comp = sum(agent.risk_compensation for agent in local_agents) / population
        multiplier = (1 - mean_distancing * params.distancing_contact_strength) * (
            1 + mean_risk_comp * _RISK_COMPENSATION_STRENGTH
        )
        return max(0.05, multiplier)
