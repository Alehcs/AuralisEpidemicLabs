"""Typed simulation API input and output schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SimulationCreateRequest(BaseModel):
    """Config references and random seed needed to create a simulation."""

    scenario_config: str = Field(default="district_v1_market_outbreak", min_length=1)
    disease_config: str = Field(default="respiratory_like_v1", min_length=1)
    population_config: str = Field(default="default_population_v1", min_length=1)
    policy_config: str | None = "local_alert_policy"
    policy_configs: list[str] = Field(default_factory=list)
    information_configs: list[str] = Field(default_factory=list)
    behavior_config: str | None = None
    adaptive_policy_config: str | None = None
    seed: int = Field(default=42, ge=0)


class SimulationRunRequest(BaseModel):
    """Bounded number of ticks to advance in one synchronous request."""

    ticks: int = Field(default=24, gt=0, le=10_000)


class MetricsSnapshotResponse(BaseModel):
    tick: int
    susceptible_count: int
    exposed_count: int
    infected_asymptomatic_count: int
    infected_symptomatic_count: int
    recovered_count: int
    isolated_count: int
    new_infections: int
    active_infections: int
    cumulative_infections: int
    active_policy_count: int
    agents_under_local_alert: int
    agents_under_global_alert: int
    mean_perceived_risk: float = Field(ge=0, le=1)
    mean_alert_exposure: float = Field(ge=0, le=1)
    mean_contacts: float = Field(ge=0)
    movement_reduction_estimate: float = Field(ge=0, le=1)
    contact_reduction_estimate: float = Field(ge=0, le=1)
    mean_real_risk: float = Field(default=0.0, ge=0, le=1)
    mean_perception_gap: float = Field(default=0.0, ge=-1, le=1)
    mean_trust_authority: float = Field(default=0.0, ge=0, le=1)
    mean_trust_peers: float = Field(default=0.0, ge=0, le=1)
    mean_fatigue: float = Field(default=0.0, ge=0, le=1)
    mean_fear: float = Field(default=0.0, ge=0, le=1)
    mean_curiosity: float = Field(default=0.0, ge=0, le=1)
    mean_compliance: float = Field(default=0.0, ge=0, le=1)
    mean_rumor_belief: float = Field(default=0.0, ge=0, le=1)
    mean_rumor_exposure: float = Field(default=0.0, ge=0, le=1)
    rumor_exposure_count: int = Field(default=0, ge=0)
    official_alert_exposure_count: int = Field(default=0, ge=0)
    false_safety_exposure_count: int = Field(default=0, ge=0)
    anti_authority_exposure_count: int = Field(default=0, ge=0)
    mean_protection_behavior: float = Field(default=0.0, ge=0, le=1)
    mean_distancing_behavior: float = Field(default=0.0, ge=0, le=1)
    mean_risk_compensation: float = Field(default=0.0, ge=0, le=1)
    mean_risky_optional_movement_bias: float = Field(default=0.0, ge=0, le=1)
    mean_peer_rumor_exposure: float = Field(default=0.0, ge=0, le=1)
    mean_peer_warning_exposure: float = Field(default=0.0, ge=0, le=1)
    raw_contact_count: int = Field(default=0, ge=0)
    effective_contact_count: int = Field(default=0, ge=0)
    effective_beta_mean: float = Field(default=0.0, ge=0)
    behavioral_transmission_reduction: float = Field(default=0.0, ge=0, le=1)
    misinformation_transmission_amplification: float = Field(default=0.0, ge=0)
    rumor_pressure: float = Field(default=0.0, ge=0, le=1)
    peer_warning_pressure: float = Field(default=0.0, ge=0, le=1)
    adaptive_policy_trigger_count: int = Field(default=0, ge=0)
    adaptive_policy_active_count: int = Field(default=0, ge=0)
    counter_messaging_active: bool = False
    peer_warning_campaign_active: bool = False
    trust_repair_active: bool = False
    adaptive_isolation_active: bool = False
    last_triggered_adaptive_rule: str | None = None
    policy_effect_summary: dict[str, Any]
    adaptive_policy_effect_summary: dict[str, Any] = Field(default_factory=dict)


class ZoneSummaryResponse(BaseModel):
    zone_id: str
    population: int
    susceptible: int
    exposed: int
    infected: int
    recovered: int
    risk_level_simple: float = Field(ge=0, le=1)
    mean_perceived_risk: float = Field(ge=0, le=1)
    mean_alert_exposure: float = Field(ge=0, le=1)
    mean_rumor_exposure: float = Field(default=0.0, ge=0, le=1)
    mean_fatigue: float = Field(default=0.0, ge=0, le=1)
    active_policies: list[str]


class SampleAgentResponse(BaseModel):
    id: str
    zone_id: str
    state: str
    profile: str
    routine_type: str
    home_zone_id: str
    intended_destination: str | None
    perceived_risk: float = Field(ge=0, le=1)
    real_risk: float = Field(default=0.0, ge=0, le=1)
    alert_exposure: float = Field(ge=0, le=1)
    rumor_exposure: float = Field(default=0.0, ge=0, le=1)
    compliance_tendency: float = Field(ge=0, le=1)
    adaptive_compliance: float = Field(default=0.0, ge=0, le=1)
    trust_authority: float = Field(default=0.0, ge=0, le=1)
    fatigue: float = Field(default=0.0, ge=0, le=1)
    protection_behavior: float = Field(default=0.0, ge=0, le=1)
    distancing_behavior: float = Field(default=0.0, ge=0, le=1)
    risk_compensation: float = Field(default=0.0, ge=0, le=1)
    peer_rumor_exposure: float = Field(default=0.0, ge=0, le=1)
    peer_warning_exposure: float = Field(default=0.0, ge=0, le=1)


class SimulationTimeResponse(BaseModel):
    tick: int
    tick_minutes: int
    day: int
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    time_of_day_label: str


class ContactRecordResponse(BaseModel):
    tick: int
    zone_id: str
    contact_count: int
    susceptible_exposed_contacts: int
    infectious_contacts: int
    new_infections: int
    average_zone_density: float


class SimulationSnapshotResponse(BaseModel):
    simulation_id: str
    tick: int = Field(ge=0)
    day: float = Field(ge=0)
    time: SimulationTimeResponse
    agents_summary: dict[str, int]
    zone_summary: list[ZoneSummaryResponse]
    contact_summary: list[ContactRecordResponse]
    active_policies: list[str]
    metrics: MetricsSnapshotResponse
    sample_agents_for_visualization: list[SampleAgentResponse]


class SimulationStateResponse(BaseModel):
    """Current simulation status and frontend-ready snapshot."""

    simulation_id: str
    status: str
    current_step: int = Field(ge=0)
    message: str
    snapshot: SimulationSnapshotResponse


class SimulationMetricsResponse(BaseModel):
    """Metric history accumulated since simulation creation."""

    simulation_id: str
    history: list[MetricsSnapshotResponse]


class PolicyStatusResponse(BaseModel):
    id: str
    name: str
    type: str
    scope: str
    target_zone_id: str | None
    active: bool
    start_tick: int
    end_tick: int | None
    intensity: float


class SimulationPoliciesResponse(BaseModel):
    simulation_id: str
    tick: int
    configured: list[PolicyStatusResponse]
    active_policy_ids: list[str]
    effect_summary: dict[str, Any]


class CognitionMetricsResponse(BaseModel):
    """Aggregate socio-cognitive measurements for the current tick."""

    mean_perceived_risk: float
    mean_real_risk: float
    mean_perception_gap: float
    mean_trust_authority: float
    mean_trust_peers: float
    mean_fatigue: float
    mean_fear: float
    mean_curiosity: float
    mean_compliance: float
    mean_rumor_belief: float


class SimulationCognitionResponse(BaseModel):
    """Cognition summary plus a bounded agent sample for inspection."""

    simulation_id: str
    tick: int
    metrics: CognitionMetricsResponse
    sample_agents: list[SampleAgentResponse]


class InformationEventStatus(BaseModel):
    id: str
    event_type: str
    source: str
    scope: str
    target_zone_id: str | None
    active: bool
    start_tick: int
    end_tick: int | None
    intensity: float
    reach: float
    accuracy: float


class SimulationInformationResponse(BaseModel):
    """Configured information events and current exposure reach."""

    simulation_id: str
    tick: int
    events: list[InformationEventStatus]
    active_information_ids: list[str]
    exposure: dict[str, int]
    effect_summary: dict[str, Any]


class BehaviorMetricsResponse(BaseModel):
    """Aggregate behavior and transmission-feedback measurements."""

    mean_protection_behavior: float
    mean_distancing_behavior: float
    mean_risk_compensation: float
    mean_risky_optional_movement_bias: float
    raw_contact_count: int
    effective_contact_count: int
    effective_beta_mean: float
    behavioral_transmission_reduction: float
    misinformation_transmission_amplification: float


class SimulationBehaviorResponse(BaseModel):
    """Behavior aggregates plus a bounded agent sample for inspection."""

    simulation_id: str
    tick: int
    metrics: BehaviorMetricsResponse
    sample_agents: list[SampleAgentResponse]


class SimulationSocialResponse(BaseModel):
    """District and per-zone social-influence pressures."""

    simulation_id: str
    tick: int
    mean_rumor_pressure: float
    mean_peer_warning_pressure: float
    mean_peer_rumor_exposure: float
    mean_peer_warning_exposure: float
    zone_pressures: dict[str, dict[str, float]]


class ActiveInterventionResponse(BaseModel):
    rule_id: str
    action: str
    target: str
    target_zone_id: str | None
    intensity: float
    start_tick: int
    end_tick: int


class AdaptiveRuleResponse(BaseModel):
    id: str
    metric: str
    operator: str
    threshold: float
    action: str
    target: str
    target_zone_id: str | None
    duration_ticks: int
    intensity: float
    cooldown_ticks: int


class SimulationAdaptiveResponse(BaseModel):
    """Configured adaptive rules and current adaptive intervention state."""

    simulation_id: str
    tick: int
    policy_id: str | None
    rules: list[AdaptiveRuleResponse]
    active_interventions: list[ActiveInterventionResponse]
    trigger_count: int
    last_triggered_rule: str | None
    effect_summary: dict[str, Any]


class ExportRunResponse(BaseModel):
    run_id: str
    directory: str
    files: list[str]


class RunSummaryResponse(BaseModel):
    run_id: str
    simulation_id: str
    tick: int
    exported_at: str


class ReplaySnapshotsResponse(BaseModel):
    run_id: str
    snapshots: list[dict[str, Any]]
