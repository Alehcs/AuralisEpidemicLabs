"""Declarative configuration schemas for simulations and experiments."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ZoneConfig(BaseModel):
    """A configured district zone and its coarse capacity."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    capacity: int = Field(gt=0)


class ScenarioConfig(BaseModel):
    """Top-level world layout and initial scenario metadata."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    duration_steps: int = Field(default=168, gt=0)
    zones: list[ZoneConfig] = Field(min_length=1)


class DiseaseConfig(BaseModel):
    """Minimal disease profile used to seed future transmission models."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    transmission_probability: float = Field(ge=0, le=1)
    incubation_days: float = Field(gt=0)
    infectious_days: float = Field(gt=0)
    severe_case_probability: float = Field(default=0.05, ge=0, le=1)


class AgentProfileDistribution(BaseModel):
    """Relative weight assigned to one socio-cognitive archetype."""

    profile: str = Field(min_length=1)
    proportion: float = Field(gt=0, le=1)


class AgentPopulationConfig(BaseModel):
    """Population size and initial behavioral profile distribution."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    population_size: int = Field(gt=0)
    profiles: list[AgentProfileDistribution] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_profile_distribution(self) -> "AgentPopulationConfig":
        total = sum(item.proportion for item in self.profiles)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("profile proportions must sum to 1.0")
        return self


class PolicyConfig(BaseModel):
    """A declarative intervention and its activation parameters."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scope: Literal["global", "local"]
    trigger: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)


class ExperimentVariantConfig(BaseModel):
    """One named treatment arm in a batch experiment."""

    id: str = Field(min_length=1)
    policy_config: str = Field(min_length=1)
    overrides: dict[str, Any] = Field(default_factory=dict)


class ExperimentConfig(BaseModel):
    """Batch comparison tying scenario, disease, population, and variants."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scenario_config: str = Field(min_length=1)
    disease_config: str = Field(min_length=1)
    population_config: str = Field(min_length=1)
    repetitions: int = Field(default=1, gt=0)
    variants: list[ExperimentVariantConfig] = Field(min_length=1)
