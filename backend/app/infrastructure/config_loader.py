"""JSON configuration adapter rooted at the repository configs directory."""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.errors import ConfigNotFoundError

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
        with path.open(encoding="utf-8") as config_file:
            payload = json.load(config_file)
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

        return model.model_validate(self.load_json(category, name))

    def _category_directory(self, category: str) -> Path:
        if category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported config category: {category}")
        return (self.base_directory / category).resolve()
