"""Simulation aggregate state and serializable domain snapshots."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.adaptive import AdaptivePolicy
from app.domain.agent import Agent
from app.domain.behavior_params import BehaviorParameters
from app.domain.contacts import ContactRecord
from app.domain.disease import DiseaseProfile
from app.domain.information import InformationEvent
from app.domain.metrics import MetricsSnapshot, ZoneMetricsSnapshot
from app.domain.policy import Policy
from app.domain.time import SimulationTime
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
    config_summary: dict[str, Any] = field(default_factory=dict)
    policy: Policy | None = None
    policies: list[Policy] = field(default_factory=list)
    information_events: list[InformationEvent] = field(default_factory=list)
    behavior_params: BehaviorParameters = field(default_factory=BehaviorParameters)
    adaptive_policy: AdaptivePolicy | None = None
    new_infections: int = 0
    metrics_history: list[MetricsSnapshot] = field(default_factory=list)
    contact_history: list[ContactRecord] = field(default_factory=list)
    snapshots_history: list[dict[str, Any]] = field(default_factory=list)
    active_policy_ids: list[str] = field(default_factory=list)
    active_information_ids: list[str] = field(default_factory=list)
    policy_effect_summary: dict[str, Any] = field(default_factory=dict)
    information_effect_summary: dict[str, Any] = field(default_factory=dict)
    movement_reduction_estimate: float = 0.0
    contact_reduction_estimate: float = 0.0
    agents_under_local_alert: int = 0
    agents_under_global_alert: int = 0
    agents_under_rumor: int = 0
    raw_contact_count: int = 0
    effective_contact_count: int = 0
    effective_beta_mean: float = 0.0
    behavioral_transmission_reduction: float = 0.0
    misinformation_transmission_amplification: float = 0.0
    rumor_pressure: float = 0.0
    peer_warning_pressure: float = 0.0
    zone_social_pressures: dict[str, dict[str, float]] = field(default_factory=dict)
    adaptive_policy_trigger_count: int = 0
    adaptive_policy_active_count: int = 0
    counter_messaging_active: bool = False
    peer_warning_campaign_active: bool = False
    trust_repair_active: bool = False
    adaptive_isolation_active: bool = False
    last_triggered_adaptive_rule: str | None = None
    adaptive_policy_effect_summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimulationSnapshot:
    """Read-only projection suitable for APIs and frontend visualization."""

    simulation_id: str
    tick: int
    day: float
    time: SimulationTime
    agents_summary: dict[str, int]
    zone_summary: list[ZoneMetricsSnapshot]
    contact_summary: list[ContactRecord]
    active_policies: list[str]
    metrics: MetricsSnapshot
    sample_agents_for_visualization: list[dict[str, Any]]
