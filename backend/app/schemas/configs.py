"""Declarative configuration schemas for simulations and experiments."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.adaptive import AdaptiveAction
from app.domain.information import InformationType
from app.domain.policy import PolicyType


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


class CognitiveDistributionConfig(BaseModel):
    """Initial population means for Phase 4 socio-cognitive attributes.

    Every field is optional with an interpretable default so existing population
    configs keep working unchanged. ``spread`` is the deterministic +/- jitter
    band applied per agent from a dedicated seeded stream.
    """

    trust_authority_mean: float = Field(default=0.55, ge=0, le=1)
    trust_peers_mean: float = Field(default=0.5, ge=0, le=1)
    fatigue_mean: float = Field(default=0.0, ge=0, le=1)
    skepticism_mean: float = Field(default=0.3, ge=0, le=1)
    curiosity_mean: float = Field(default=0.3, ge=0, le=1)
    rumor_belief_mean: float = Field(default=0.3, ge=0, le=1)
    compliance_mean: float = Field(default=0.5, ge=0, le=1)
    spread: float = Field(default=0.12, ge=0, le=0.5)


class BehavioralProfileConfig(BaseModel):
    """Additive per-profile biases layered on the population cognitive means."""

    trust_authority: float = Field(default=0.0, ge=-1, le=1)
    trust_peers: float = Field(default=0.0, ge=-1, le=1)
    fatigue: float = Field(default=0.0, ge=-1, le=1)
    skepticism: float = Field(default=0.0, ge=-1, le=1)
    curiosity: float = Field(default=0.0, ge=-1, le=1)
    rumor_belief: float = Field(default=0.0, ge=-1, le=1)
    compliance: float = Field(default=0.0, ge=-1, le=1)


class AgentPopulationConfig(BaseModel):
    """Population size and initial behavioral profile distribution."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    population_size: int = Field(gt=0)
    profiles: list[AgentProfileDistribution] = Field(min_length=1)
    routines: list[RoutineDistribution] = Field(min_length=1)
    cognition: CognitiveDistributionConfig = Field(
        default_factory=CognitiveDistributionConfig
    )
    behavioral_profiles: dict[str, BehavioralProfileConfig] = Field(default_factory=dict)

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
    policy_type: PolicyType = PolicyType.LOCAL_ALERT
    intensity: float = Field(default=0.5, ge=0, le=1)
    start_tick: int = Field(default=0, ge=0)
    end_tick: int | None = Field(default=None, ge=0)
    target_zone_id: str | None = None
    compliance_requirement: float = Field(default=0.0, ge=0, le=1)
    mobility_impact: float | None = Field(default=None, ge=0, le=1)
    contact_impact: float | None = Field(default=None, ge=0, le=1)
    transmission_impact: float | None = Field(default=None, ge=0, le=1)
    trigger: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)

    @field_validator("policy_type", mode="before")
    @classmethod
    def normalize_policy_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.lower()
            return PolicyType.LOCAL_ALERT if normalized == "alert" else normalized
        return value

    @model_validator(mode="after")
    def validate_schedule(self) -> "PolicyConfig":
        if self.end_tick is not None and self.end_tick < self.start_tick:
            raise ValueError("policy end_tick must be greater than or equal to start_tick")
        if self.scope == "local" and not self.target_zone_id:
            raise ValueError("local policies require target_zone_id")
        if self.policy_type in {PolicyType.LOCAL_ALERT, PolicyType.ZONE_CLOSURE} and not self.target_zone_id:
            raise ValueError(f"{self.policy_type.value} policies require target_zone_id")
        return self

    def resolved_impact(self, name: str, default: float = 0.0) -> float:
        """Read an explicit impact or its backward-compatible effects value."""

        explicit = getattr(self, name)
        if explicit is not None:
            return explicit
        legacy_names = {
            "mobility_impact": "mobility_reduction",
            "contact_impact": "contact_reduction",
            "transmission_impact": "transmission_reduction",
        }
        return float(self.effects.get(legacy_names[name], default))


class InformationEventConfig(BaseModel):
    """A declarative official message or rumor with a fixed schedule."""

    id: str = Field(min_length=1)
    event_type: InformationType
    source: str = Field(default="unknown", min_length=1)
    start_tick: int = Field(default=0, ge=0)
    end_tick: int | None = Field(default=None, ge=0)
    target_zone_id: str | None = None
    intensity: float = Field(default=0.5, ge=0, le=1)
    reach: float = Field(default=0.5, ge=0, le=1)
    accuracy: float = Field(default=0.5, ge=0, le=1)
    decay_rate: float = Field(default=0.05, ge=0, le=1)

    @field_validator("event_type", mode="before")
    @classmethod
    def normalize_event_type(cls, value: Any) -> Any:
        return value.lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_schedule(self) -> "InformationEventConfig":
        if self.end_tick is not None and self.end_tick < self.start_tick:
            raise ValueError("information event end_tick must be >= start_tick")
        return self


class BehaviorConfig(BaseModel):
    """Tunable behavior/transmission strengths (Phase 6).

    Defaults match the Phase 5 module constants, so omitting a behavior config
    reproduces earlier behavior exactly. Upper bounds are generous to allow
    sensitivity sweeps above the calibrated baseline.
    """

    id: str = Field(min_length=1)
    name: str = Field(default="Behavior parameters", min_length=1)
    susceptible_protection_strength: float = Field(default=0.6, ge=0, le=5)
    infectious_protection_strength: float = Field(default=0.5, ge=0, le=5)
    risk_compensation_strength: float = Field(default=0.6, ge=0, le=5)
    distancing_contact_strength: float = Field(default=0.5, ge=0, le=5)
    false_safety_amplification_strength: float = Field(default=0.45, ge=0, le=5)
    anti_authority_compliance_penalty: float = Field(default=0.15, ge=0, le=5)
    fatigue_protection_penalty: float = Field(default=0.35, ge=0, le=1)
    peer_warning_protection_boost: float = Field(default=0.0, ge=0, le=5)


BEHAVIOR_PARAMETER_FIELDS = frozenset(
    BehaviorConfig.model_fields.keys() - {"id", "name"}
)


class AdaptiveRuleConfig(BaseModel):
    """A single metric-triggered adaptive intervention rule."""

    id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    operator: Literal[">", "<", ">=", "<=", "=="]
    threshold: float
    action: AdaptiveAction
    target: Literal["global", "local"] = "global"
    target_zone_id: str | None = None
    duration_ticks: int = Field(default=24, gt=0)
    intensity: float = Field(default=0.5, ge=0, le=1)
    cooldown_ticks: int = Field(default=24, ge=0)

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: Any) -> Any:
        return value.lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_target(self) -> "AdaptiveRuleConfig":
        if self.target == "local" and not self.target_zone_id:
            raise ValueError("local adaptive rules require target_zone_id")
        return self


class AdaptivePolicyConfig(BaseModel):
    """A named bundle of adaptive rules."""

    id: str = Field(min_length=1)
    name: str = Field(default="Adaptive policy", min_length=1)
    rules: list[AdaptiveRuleConfig] = Field(min_length=1)


class ExperimentVariantConfig(BaseModel):
    """One named treatment arm in a batch experiment."""

    id: str = Field(min_length=1)
    policy_config: str | None = None
    policy_configs: list[str] = Field(default_factory=list)
    information_configs: list[str] = Field(default_factory=list)
    behavior_config: str | None = None
    adaptive_policy_config: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_references(self) -> "ExperimentVariantConfig":
        if self.policy_config and self.policy_configs:
            raise ValueError("use policy_config or policy_configs, not both")
        return self


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
    behavior_config: str | None = None
    variants: list[ExperimentVariantConfig] = Field(min_length=1)


class SweepConfig(BaseModel):
    """A deterministic parameter-sweep over behavior strengths for an experiment."""

    id: str = Field(min_length=1)
    name: str = Field(default="Parameter sweep", min_length=1)
    experiment_config: str = Field(min_length=1)
    parameter_grid: dict[str, list[float]] = Field(min_length=1)
    seeds: list[int] | None = None
    ticks: int | None = Field(default=None, gt=0, le=100_000)
    population_size: int | None = Field(default=None, gt=0)
    focus_variant: str | None = None

    @model_validator(mode="after")
    def validate_grid(self) -> "SweepConfig":
        for name, values in self.parameter_grid.items():
            if name not in BEHAVIOR_PARAMETER_FIELDS:
                raise ValueError(f"unknown sweep parameter: {name}")
            if not values:
                raise ValueError(f"sweep parameter '{name}' must list at least one value")
        return self
