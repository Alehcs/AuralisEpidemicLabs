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
