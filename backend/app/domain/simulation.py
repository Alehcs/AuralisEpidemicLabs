"""Simulation aggregate state and serializable domain snapshots."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.agent import Agent
from app.domain.disease import DiseaseProfile
from app.domain.metrics import MetricsSnapshot, ZoneMetricsSnapshot
from app.domain.world import World


@dataclass(slots=True)
class SimulationState:
    """Mutable aggregate owned by one deterministic simulation engine."""

    simulation_id: str
    seed: int
    tick: int
    world: World
    disease: DiseaseProfile
    agents: list[Agent]
    cumulative_infections: int
    new_infections: int = 0
    metrics_history: list[MetricsSnapshot] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SimulationSnapshot:
    """Read-only projection suitable for APIs and frontend visualization."""

    simulation_id: str
    tick: int
    day: float
    agents_summary: dict[str, int]
    zone_summary: list[ZoneMetricsSnapshot]
    metrics: MetricsSnapshot
    sample_agents_for_visualization: list[dict[str, Any]]
