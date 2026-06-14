"""Aggregate explicit contact records without materializing all pairs."""

from collections import Counter, defaultdict
from dataclasses import dataclass

from app.domain.agent import Agent
from app.domain.contacts import ContactRecord
from app.domain.world import World
from app.simulation.policies import PolicyModifiers


@dataclass(slots=True)
class ZoneContactContext:
    """Agents and infectious pressure currently co-located in one zone."""

    zone_id: str
    agents: list[Agent]
    infectious_pressure: float


@dataclass(slots=True)
class ContactBatch:
    """Contexts used for transmission and compact records retained for replay."""

    contexts: dict[str, ZoneContactContext]
    records: list[ContactRecord]
    baseline_contact_count: int = 0
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
    ) -> ContactBatch:
        modifiers = policy_modifiers or PolicyModifiers()
        grouped: dict[str, list[Agent]] = defaultdict(list)
        for agent in agents:
            grouped[agent.zone_id].append(agent)

        contexts: dict[str, ZoneContactContext] = {}
        records: list[ContactRecord] = []
        baseline_total = 0
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
            contact_count = round(baseline_contacts * contact_multiplier)
            baseline_total += baseline_contacts
            effective_total += contact_count
            infectious_prevalence = infectious_pressure / population
            susceptible_exposed = round(
                counts["susceptible"]
                * zone.contact_rate
                * contact_multiplier
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
            baseline_contact_count=baseline_total,
            effective_contact_count=effective_total,
        )
