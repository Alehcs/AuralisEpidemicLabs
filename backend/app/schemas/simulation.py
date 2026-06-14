"""Typed simulation API input and output schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SimulationCreateRequest(BaseModel):
    """Config references and random seed needed to create a simulation."""

    scenario_config: str = Field(default="district_v1_market_outbreak", min_length=1)
    disease_config: str = Field(default="respiratory_like_v1", min_length=1)
    population_config: str = Field(default="default_population_v1", min_length=1)
    policy_config: str | None = "local_alert_policy"
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


class ZoneSummaryResponse(BaseModel):
    zone_id: str
    population: int
    susceptible: int
    exposed: int
    infected: int
    recovered: int
    risk_level_simple: float = Field(ge=0, le=1)


class SampleAgentResponse(BaseModel):
    id: str
    zone_id: str
    state: str
    profile: str


class SimulationSnapshotResponse(BaseModel):
    simulation_id: str
    tick: int = Field(ge=0)
    day: float = Field(ge=0)
    agents_summary: dict[str, int]
    zone_summary: list[ZoneSummaryResponse]
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
