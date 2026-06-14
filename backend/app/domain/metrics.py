"""Metrics captured from a simulation state."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Immutable aggregate measurements for one simulation tick."""

    tick: int
    susceptible_count: int = 0
    exposed_count: int = 0
    infected_asymptomatic_count: int = 0
    infected_symptomatic_count: int = 0
    recovered_count: int = 0
    isolated_count: int = 0
    new_infections: int = 0
    active_infections: int = 0
    cumulative_infections: int = 0


@dataclass(frozen=True, slots=True)
class ZoneMetricsSnapshot:
    """Aggregate state and simple local risk for one district zone."""

    zone_id: str
    population: int
    susceptible: int
    exposed: int
    infected: int
    recovered: int
    risk_level_simple: float
