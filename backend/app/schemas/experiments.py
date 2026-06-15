"""Batch experiment request and result schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ExperimentRunRequest(BaseModel):
    experiment_config: str = Field(default="global_vs_local_alert", min_length=1)


class SweepRunRequest(BaseModel):
    sweep_config: str = Field(default="behavior_sensitivity_v1", min_length=1)


class SweepPointResult(BaseModel):
    point_index: int
    parameters: dict[str, float]
    variants: list[dict[str, Any]]
    focus_metrics: dict[str, float]


class SweepResultResponse(BaseModel):
    sweep_id: str
    status: str
    experiment_config: str
    parameter_grid: dict[str, list[float]]
    focus_variant: str
    points: list[SweepPointResult]
    best_response: dict[str, Any]
    report: dict[str, Any]


class ExperimentRunMetric(BaseModel):
    final_susceptible: int
    final_exposed: int
    final_infected: int
    final_recovered: int
    cumulative_infections: int
    peak_active_infections: int
    tick_of_peak: int
    mean_perceived_risk: float
    mean_alert_exposure: float
    mean_contacts: float
    mean_movement_reduction: float
    mean_contact_reduction: float
    mean_real_risk: float = 0.0
    mean_perception_gap: float = 0.0
    mean_trust_authority: float = 0.0
    mean_fatigue: float = 0.0
    mean_compliance: float = 0.0
    mean_rumor_exposure: float = 0.0
    mean_protection_behavior: float = 0.0
    mean_distancing_behavior: float = 0.0
    mean_risk_compensation: float = 0.0
    effective_contact_count: float = 0.0
    effective_beta_mean: float = 0.0
    behavioral_transmission_reduction: float = 0.0
    misinformation_transmission_amplification: float = 0.0
    adaptive_policy_trigger_count: float = 0.0


class ExperimentRunResult(BaseModel):
    run_id: str
    variant_id: str
    seed: int
    metrics: ExperimentRunMetric


class VariantResult(BaseModel):
    variant_id: str
    runs: list[ExperimentRunResult]
    aggregate: dict[str, float]


class ExperimentResultResponse(BaseModel):
    experiment_id: str
    status: str
    ticks: int
    variants: list[VariantResult]
    report: dict[str, Any]
