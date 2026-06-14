"""Declarative configuration schemas for simulations and experiments."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ZoneConfig(BaseModel):
    """A configured district zone and its coarse capacity."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    contact_rate: float = Field(default=1.0, gt=0)
    movement_weight: float = Field(default=1.0, gt=0)


class RouteConfig(BaseModel):
    """A configured directed route between two zones."""

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    travel_weight: float = Field(default=1.0, gt=0)


class InitialOutbreakConfig(BaseModel):
    """Initial disease seeds placed in one configured zone."""

    zone_id: str = Field(min_length=1)
    exposed_agents: int = Field(default=0, ge=0)
    infected_agents: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def validate_has_seed_agents(self) -> "InitialOutbreakConfig":
        if self.exposed_agents + self.infected_agents == 0:
            raise ValueError("initial outbreak must contain at least one agent")
        return self


class ScenarioConfig(BaseModel):
    """Top-level world layout and initial scenario metadata."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    duration_steps: int = Field(default=168, gt=0)
    zones: list[ZoneConfig] = Field(min_length=1)
    routes: list[RouteConfig] = Field(min_length=1)
    initial_outbreak: InitialOutbreakConfig

    @model_validator(mode="after")
    def validate_zone_references(self) -> "ScenarioConfig":
        zone_ids = {zone.id for zone in self.zones}
        if len(zone_ids) != len(self.zones):
            raise ValueError("zone ids must be unique")
        if self.initial_outbreak.zone_id not in zone_ids:
            raise ValueError("initial outbreak zone must exist in scenario zones")
        for route in self.routes:
            if route.origin not in zone_ids or route.destination not in zone_ids:
                raise ValueError("route endpoints must exist in scenario zones")
            if route.origin == route.destination:
                raise ValueError("route endpoints must be different")
        return self


class DiseaseConfig(BaseModel):
    """Minimal disease profile used to seed future transmission models."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    beta_base: float = Field(gt=0, le=1)
    incubation_days: float = Field(gt=0)
    infectious_days: float = Field(gt=0)
    asymptomatic_probability: float = Field(default=0.4, ge=0, le=1)
    tick_minutes: int = Field(default=60, gt=0, le=1440)


class AgentProfileDistribution(BaseModel):
    """Relative weight assigned to one socio-cognitive archetype."""

    profile: str = Field(min_length=1)
    proportion: float = Field(gt=0, le=1)


class RoutineDistribution(BaseModel):
    """Relative population weight for one schedule archetype."""

    routine_type: Literal[
        "worker",
        "student",
        "remote",
        "elderly",
        "trader",
        "healthcare",
        "unemployed",
    ]
    proportion: float = Field(gt=0, le=1)


class AgentPopulationConfig(BaseModel):
    """Population size and initial behavioral profile distribution."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    population_size: int = Field(gt=0)
    profiles: list[AgentProfileDistribution] = Field(min_length=1)
    routines: list[RoutineDistribution] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_profile_distribution(self) -> "AgentPopulationConfig":
        total = sum(item.proportion for item in self.profiles)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("profile proportions must sum to 1.0")
        routine_total = sum(item.proportion for item in self.routines)
        if abs(routine_total - 1.0) > 1e-6:
            raise ValueError("routine proportions must sum to 1.0")
        return self


class PolicyConfig(BaseModel):
    """A declarative intervention and its activation parameters."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scope: Literal["global", "local"]
    policy_type: str = Field(default="alert", min_length=1)
    intensity: float = Field(default=0.5, ge=0, le=1)
    start_tick: int = Field(default=0, ge=0)
    end_tick: int | None = Field(default=None, ge=0)
    target_zone_id: str | None = None
    trigger: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schedule(self) -> "PolicyConfig":
        if self.end_tick is not None and self.end_tick < self.start_tick:
            raise ValueError("policy end_tick must be greater than or equal to start_tick")
        if self.scope == "local" and not self.target_zone_id:
            raise ValueError("local policies require target_zone_id")
        return self


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
    seeds: list[int] = Field(default_factory=lambda: [42], min_length=1)
    ticks: int = Field(default=168, gt=0, le=100_000)
    variants: list[ExperimentVariantConfig] = Field(min_length=1)
