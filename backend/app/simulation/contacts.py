"""Aggregate zone-level contact contexts without pairwise materialization."""

from collections import defaultdict
from dataclasses import dataclass

from app.domain.agent import Agent


@dataclass(slots=True)
class ZoneContactContext:
    """Agents and infectious pressure currently co-located in one zone."""

    zone_id: str
    agents: list[Agent]
    infectious_pressure: float


class ContactEngine:
    """Build O(n) local contact contexts for the transmission engine."""

    def step(self, agents: list[Agent]) -> dict[str, ZoneContactContext]:
        """Group agents by zone and aggregate their infectiousness."""

        grouped: dict[str, list[Agent]] = defaultdict(list)
        for agent in agents:
            grouped[agent.zone_id].append(agent)
        return {
            zone_id: ZoneContactContext(
                zone_id=zone_id,
                agents=local_agents,
                infectious_pressure=sum(
                    agent.infectiousness for agent in local_agents if agent.is_infectious
                ),
            )
            for zone_id, local_agents in grouped.items()
        }
