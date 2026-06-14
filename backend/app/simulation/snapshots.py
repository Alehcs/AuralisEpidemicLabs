"""Serializable simulation state snapshots."""

from dataclasses import asdict

from app.domain.simulation import SimulationSnapshot, SimulationState
from app.domain.time import SimulationTime
from app.simulation.metrics import MetricsEngine


class SnapshotBuilder:
    """Build stable snapshots for APIs, files, and future replay tooling."""

    def __init__(self, metrics_engine: MetricsEngine | None = None) -> None:
        self.metrics_engine = metrics_engine or MetricsEngine()

    def create_snapshot(self, state: SimulationState) -> SimulationSnapshot:
        """Create a compact deterministic projection of current state."""

        metrics = state.metrics_history[-1]
        simulation_time = SimulationTime.from_tick(state.tick, state.disease.tick_minutes)
        zone_summary = self.metrics_engine.create_zone_snapshots(state.agents, state.world)
        contact_summary = [record for record in state.contact_history if record.tick == state.tick]
        sample = [
            {
                "id": agent.id,
                "zone_id": agent.zone_id,
                "state": agent.state.value,
                "profile": agent.profile,
                "routine_type": agent.routine_type.value,
                "home_zone_id": agent.home_zone_id,
                "intended_destination": agent.current_intended_destination,
            }
            for agent in state.agents[:120]
        ]
        agents_summary = {
            "susceptible": metrics.susceptible_count,
            "exposed": metrics.exposed_count,
            "infected_asymptomatic": metrics.infected_asymptomatic_count,
            "infected_symptomatic": metrics.infected_symptomatic_count,
            "recovered": metrics.recovered_count,
            "isolated": metrics.isolated_count,
        }
        return SimulationSnapshot(
            simulation_id=state.simulation_id,
            tick=state.tick,
            day=round(state.tick * state.disease.tick_minutes / 1440, 4),
            time=simulation_time,
            agents_summary=agents_summary,
            zone_summary=zone_summary,
            contact_summary=contact_summary,
            active_policies=state.active_policy_ids,
            metrics=metrics,
            sample_agents_for_visualization=sample,
        )

    @staticmethod
    def as_dict(snapshot: SimulationSnapshot) -> dict[str, object]:
        """Convert a domain snapshot to JSON-compatible primitives."""

        return asdict(snapshot)
