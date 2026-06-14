"""Simulation API input and output schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SimulationCreateRequest(BaseModel):
    """References to declarative configs needed to create a simulation."""

    scenario_config: str = Field(min_length=1)
    disease_config: str = Field(min_length=1)
    population_config: str = Field(min_length=1)
    policy_config: str | None = None
    seed: int | None = Field(default=None, ge=0)


class SimulationStateResponse(BaseModel):
    """Transport representation of the current coarse simulation state."""

    simulation_id: str
    status: str
    current_step: int = Field(ge=0)
    message: str
    snapshot: dict[str, Any] = Field(default_factory=dict)
