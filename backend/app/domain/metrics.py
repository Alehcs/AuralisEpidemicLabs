"""Metrics captured from a simulation state."""

from dataclasses import dataclass, field
from typing import Any


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
    active_policy_count: int = 0
    agents_under_local_alert: int = 0
    agents_under_global_alert: int = 0
    mean_perceived_risk: float = 0.0
    mean_alert_exposure: float = 0.0
    mean_contacts: float = 0.0
    movement_reduction_estimate: float = 0.0
    contact_reduction_estimate: float = 0.0
    policy_effect_summary: dict[str, Any] = field(default_factory=dict)


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
    mean_perceived_risk: float = 0.0
    mean_alert_exposure: float = 0.0
    active_policies: tuple[str, ...] = ()
