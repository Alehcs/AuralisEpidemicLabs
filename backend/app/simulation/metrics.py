"""Aggregate metric computation boundary."""

from collections import Counter
from statistics import fmean

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
        active_policy_count: int = 0,
        agents_under_local_alert: int = 0,
        agents_under_global_alert: int = 0,
        contact_count: int = 0,
        movement_reduction_estimate: float = 0.0,
        contact_reduction_estimate: float = 0.0,
        policy_effect_summary: dict[str, object] | None = None,
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
            active_policy_count=active_policy_count,
            agents_under_local_alert=agents_under_local_alert,
            agents_under_global_alert=agents_under_global_alert,
            mean_perceived_risk=round(fmean(agent.perceived_risk for agent in agents), 6),
            mean_alert_exposure=round(fmean(agent.alert_exposure for agent in agents), 6),
            mean_contacts=round((contact_count * 2) / len(agents), 6),
            movement_reduction_estimate=round(movement_reduction_estimate, 6),
            contact_reduction_estimate=round(contact_reduction_estimate, 6),
            policy_effect_summary=policy_effect_summary or {},
        )

    def create_zone_snapshots(
        self,
        agents: list[Agent],
        world: World,
        active_policy_ids_by_zone: dict[str, tuple[str, ...]] | None = None,
    ) -> list[ZoneMetricsSnapshot]:
        """Compute local counts and active-infection ratio for each zone."""

        by_zone: dict[str, Counter[str]] = {
            zone_id: Counter() for zone_id in world.zones
        }
        for agent in agents:
            by_zone[agent.zone_id][agent.state.value] += 1

        snapshots = []
        policy_ids = active_policy_ids_by_zone or {}
        for zone_id in world.zones:
            counts = by_zone[zone_id]
            local_agents = [agent for agent in agents if agent.zone_id == zone_id]
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
                    mean_perceived_risk=(
                        round(fmean(agent.perceived_risk for agent in local_agents), 6)
                        if local_agents
                        else 0.0
                    ),
                    mean_alert_exposure=(
                        round(fmean(agent.alert_exposure for agent in local_agents), 6)
                        if local_agents
                        else 0.0
                    ),
                    active_policies=policy_ids.get(zone_id, ()),
                )
            )
        return snapshots
