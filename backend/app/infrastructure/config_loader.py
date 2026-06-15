"""JSON configuration adapter rooted at the repository configs directory."""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.errors import ConfigNotFoundError, ConfigValidationError
from app.domain.adaptive import AdaptivePolicy, AdaptiveRule
from app.domain.behavior_params import BehaviorParameters
from app.domain.disease import DiseaseProfile
from app.domain.information import InformationEvent
from app.domain.policy import Policy
from app.domain.world import Route, World, Zone
from app.schemas.configs import (
    AdaptivePolicyConfig,
    AgentPopulationConfig,
    BehaviorConfig,
    DiseaseConfig,
    ExperimentConfig,
    InformationEventConfig,
    PolicyConfig,
    ScenarioConfig,
    SweepConfig,
)

ConfigModel = TypeVar("ConfigModel", bound=BaseModel)
SUPPORTED_CATEGORIES = {
    "scenarios",
    "diseases",
    "populations",
    "policies",
    "experiments",
    "information",
    "behavior",
    "adaptive",
    "sweeps",
}


class ConfigLoader:
    """Load and validate declarative JSON configurations from disk."""

    def __init__(self, base_directory: Path | str) -> None:
        self.base_directory = Path(base_directory).resolve()

    def list_configs(self, category: str) -> list[str]:
        """List JSON config stems in a supported category."""

        directory = self._category_directory(category)
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))

    def load_json(self, category: str, name: str) -> dict[str, Any]:
        """Load one JSON object, accepting names with or without `.json`."""

        directory = self._category_directory(category)
        filename = name if name.endswith(".json") else f"{name}.json"
        path = (directory / filename).resolve()
        if path.parent != directory:
            raise ConfigNotFoundError(f"Invalid config name: {name}")
        if not path.is_file():
            raise ConfigNotFoundError(f"Config not found: {category}/{filename}")
        try:
            with path.open(encoding="utf-8") as config_file:
                payload = json.load(config_file)
        except json.JSONDecodeError as error:
            raise ConfigValidationError(
                f"Invalid JSON in {category}/{filename}: {error.msg} at line {error.lineno}"
            ) from error
        if not isinstance(payload, dict):
            raise ValueError(f"Config must contain a JSON object: {path}")
        return payload

    def load_model(
        self,
        category: str,
        name: str,
        model: type[ConfigModel],
    ) -> ConfigModel:
        """Load one config and validate it with a Pydantic schema."""

        try:
            return model.model_validate(self.load_json(category, name))
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in error.errors()
            )
            raise ConfigValidationError(f"Invalid {category} config '{name}': {details}") from error

    def load_scenario(self, name: str) -> ScenarioConfig:
        """Load and validate a scenario config."""

        return self.load_model("scenarios", name, ScenarioConfig)

    def load_disease(self, name: str) -> DiseaseConfig:
        """Load and validate a disease config."""

        return self.load_model("diseases", name, DiseaseConfig)

    def load_population(self, name: str) -> AgentPopulationConfig:
        """Load and validate a population config."""

        return self.load_model("populations", name, AgentPopulationConfig)

    def load_policy(self, name: str) -> PolicyConfig:
        """Load and validate a policy config without applying its effects yet."""

        return self.load_model("policies", name, PolicyConfig)

    def load_experiment(self, name: str) -> ExperimentConfig:
        """Load and validate an experiment config."""

        return self.load_model("experiments", name, ExperimentConfig)

    def load_information(self, name: str) -> InformationEventConfig:
        """Load and validate one official-message or rumor event config."""

        return self.load_model("information", name, InformationEventConfig)

    def load_behavior(self, name: str) -> BehaviorConfig:
        """Load and validate a behavior-strength config."""

        return self.load_model("behavior", name, BehaviorConfig)

    def load_adaptive(self, name: str) -> AdaptivePolicyConfig:
        """Load and validate an adaptive-policy config."""

        return self.load_model("adaptive", name, AdaptivePolicyConfig)

    def load_sweep(self, name: str) -> SweepConfig:
        """Load and validate a parameter-sweep config."""

        return self.load_model("sweeps", name, SweepConfig)

    @staticmethod
    def to_world(config: ScenarioConfig) -> World:
        """Convert a validated scenario into pure domain entities."""

        zones = {
            zone.id: Zone(
                id=zone.id,
                name=zone.name,
                kind=zone.kind,
                capacity=zone.capacity,
                contact_rate=zone.contact_rate,
                movement_weight=zone.movement_weight,
            )
            for zone in config.zones
        }
        routes = [
            Route(
                origin_zone_id=route.origin,
                destination_zone_id=route.destination,
                travel_weight=route.travel_weight,
            )
            for route in config.routes
        ]
        return World(zones=zones, routes=routes)

    @staticmethod
    def to_disease(config: DiseaseConfig) -> DiseaseProfile:
        """Convert a validated disease config into a domain profile."""

        return DiseaseProfile(
            id=config.id,
            name=config.name,
            beta_base=config.beta_base,
            incubation_days=config.incubation_days,
            infectious_days=config.infectious_days,
            asymptomatic_probability=config.asymptomatic_probability,
            tick_minutes=config.tick_minutes,
        )

    @staticmethod
    def to_policy(config: PolicyConfig) -> Policy:
        """Convert a validated policy config into a scheduled domain hook."""

        return Policy(
            id=config.id,
            name=config.name,
            scope=config.scope,
            policy_type=config.policy_type,
            intensity=config.intensity,
            start_tick=config.start_tick,
            end_tick=config.end_tick,
            target_zone_id=config.target_zone_id,
            compliance_requirement=config.compliance_requirement,
            mobility_impact=config.resolved_impact("mobility_impact"),
            contact_impact=config.resolved_impact("contact_impact"),
            transmission_impact=config.resolved_impact("transmission_impact"),
            parameters={"trigger": config.trigger, "effects": config.effects},
        )

    @staticmethod
    def to_behavior_parameters(config: BehaviorConfig) -> BehaviorParameters:
        """Convert a validated behavior config into immutable parameters."""

        return BehaviorParameters(
            susceptible_protection_strength=config.susceptible_protection_strength,
            infectious_protection_strength=config.infectious_protection_strength,
            risk_compensation_strength=config.risk_compensation_strength,
            distancing_contact_strength=config.distancing_contact_strength,
            false_safety_amplification_strength=config.false_safety_amplification_strength,
            anti_authority_compliance_penalty=config.anti_authority_compliance_penalty,
            fatigue_protection_penalty=config.fatigue_protection_penalty,
            peer_warning_protection_boost=config.peer_warning_protection_boost,
        )

    @staticmethod
    def to_adaptive_policy(config: AdaptivePolicyConfig) -> AdaptivePolicy:
        """Convert a validated adaptive config into a domain policy."""

        return AdaptivePolicy(
            id=config.id,
            rules=tuple(
                AdaptiveRule(
                    id=rule.id,
                    metric=rule.metric,
                    operator=rule.operator,
                    threshold=rule.threshold,
                    action=rule.action,
                    target=rule.target,
                    target_zone_id=rule.target_zone_id,
                    duration_ticks=rule.duration_ticks,
                    intensity=rule.intensity,
                    cooldown_ticks=rule.cooldown_ticks,
                )
                for rule in config.rules
            ),
        )

    @staticmethod
    def to_information_event(config: InformationEventConfig) -> InformationEvent:
        """Convert a validated information config into a scheduled domain event."""

        return InformationEvent(
            id=config.id,
            event_type=config.event_type,
            source=config.source,
            start_tick=config.start_tick,
            end_tick=config.end_tick,
            target_zone_id=config.target_zone_id,
            intensity=config.intensity,
            reach=config.reach,
            accuracy=config.accuracy,
            decay_rate=config.decay_rate,
        )

    def _category_directory(self, category: str) -> Path:
        if category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported config category: {category}")
        return (self.base_directory / category).resolve()
