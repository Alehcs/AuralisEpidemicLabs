"""Aggregate metric computation boundary."""

from collections import Counter

from app.domain.agent import Agent
from app.domain.metrics import MetricsSnapshot, ZoneMetricsSnapshot
from app.domain.world import World


class MetricsEngine:
    """Compute epidemiological and future socio-cognitive aggregates."""

    def create_snapshot(
        self,
        tick: int,
        agents: list[Agent],
        new_infections: int,
        cumulative_infections: int,
    ) -> MetricsSnapshot:
        """Count agents by state and derive active infection totals."""

        counts = Counter(agent.state.value for agent in agents)
        active = (
            counts["exposed"]
            + counts["infected_asymptomatic"]
            + counts["infected_symptomatic"]
            + counts["isolated"]
        )
        return MetricsSnapshot(
            tick=tick,
            susceptible_count=counts["susceptible"],
            exposed_count=counts["exposed"],
            infected_asymptomatic_count=counts["infected_asymptomatic"],
            infected_symptomatic_count=counts["infected_symptomatic"],
            recovered_count=counts["recovered"],
            isolated_count=counts["isolated"],
            new_infections=new_infections,
            active_infections=active,
            cumulative_infections=cumulative_infections,
        )

    def create_zone_snapshots(
        self,
        agents: list[Agent],
        world: World,
    ) -> list[ZoneMetricsSnapshot]:
        """Compute local counts and active-infection ratio for each zone."""

        by_zone: dict[str, Counter[str]] = {
            zone_id: Counter() for zone_id in world.zones
        }
        for agent in agents:
            by_zone[agent.zone_id][agent.state.value] += 1

        snapshots = []
        for zone_id in world.zones:
            counts = by_zone[zone_id]
            population = sum(counts.values())
            infected = (
                counts["infected_asymptomatic"]
                + counts["infected_symptomatic"]
                + counts["isolated"]
            )
            active = infected + counts["exposed"]
            snapshots.append(
                ZoneMetricsSnapshot(
                    zone_id=zone_id,
                    population=population,
                    susceptible=counts["susceptible"],
                    exposed=counts["exposed"],
                    infected=infected,
                    recovered=counts["recovered"],
                    risk_level_simple=round(active / population, 6) if population else 0.0,
                )
            )
        return snapshots
