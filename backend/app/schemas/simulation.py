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
    policy_effect_summary: dict[str, Any]


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
    alert_exposure: float = Field(ge=0, le=1)
    compliance_tendency: float = Field(ge=0, le=1)


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
