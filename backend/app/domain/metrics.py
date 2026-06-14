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
    # --- Phase 4 socio-cognitive and information aggregates ---
    mean_real_risk: float = 0.0
    mean_perception_gap: float = 0.0
    mean_trust_authority: float = 0.0
    mean_trust_peers: float = 0.0
    mean_fatigue: float = 0.0
    mean_fear: float = 0.0
    mean_curiosity: float = 0.0
    mean_compliance: float = 0.0
    mean_rumor_belief: float = 0.0
    mean_rumor_exposure: float = 0.0
    rumor_exposure_count: int = 0
    official_alert_exposure_count: int = 0
    false_safety_exposure_count: int = 0
    anti_authority_exposure_count: int = 0
    # --- Phase 5 behavior and transmission-feedback aggregates ---
    mean_protection_behavior: float = 0.0
    mean_distancing_behavior: float = 0.0
    mean_risk_compensation: float = 0.0
    mean_risky_optional_movement_bias: float = 0.0
    mean_peer_rumor_exposure: float = 0.0
    mean_peer_warning_exposure: float = 0.0
    raw_contact_count: int = 0
    effective_contact_count: int = 0
    effective_beta_mean: float = 0.0
    behavioral_transmission_reduction: float = 0.0
    misinformation_transmission_amplification: float = 0.0
    rumor_pressure: float = 0.0
    peer_warning_pressure: float = 0.0
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
    mean_rumor_exposure: float = 0.0
    mean_fatigue: float = 0.0
    active_policies: tuple[str, ...] = ()
