"""Batch experiment request and result schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ExperimentRunRequest(BaseModel):
    experiment_config: str = Field(default="global_vs_local_alert", min_length=1)


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
