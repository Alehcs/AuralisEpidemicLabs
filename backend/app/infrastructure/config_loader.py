"""JSON configuration adapter rooted at the repository configs directory."""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.errors import ConfigNotFoundError, ConfigValidationError
from app.domain.disease import DiseaseProfile
from app.domain.policy import Policy
from app.domain.world import Route, World, Zone
from app.schemas.configs import (
    AgentPopulationConfig,
    DiseaseConfig,
    ExperimentConfig,
    PolicyConfig,
    ScenarioConfig,
)

ConfigModel = TypeVar("ConfigModel", bound=BaseModel)
SUPPORTED_CATEGORIES = {"scenarios", "diseases", "populations", "policies", "experiments"}


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
            parameters={"trigger": config.trigger, "effects": config.effects},
        )

    def _category_directory(self, category: str) -> Path:
        if category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported config category: {category}")
        return (self.base_directory / category).resolve()
