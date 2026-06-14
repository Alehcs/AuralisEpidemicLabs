"""Use cases for discovering and reading declarative configs."""

from typing import Any

from app.infrastructure.config_loader import ConfigLoader, SUPPORTED_CATEGORIES


class ConfigService:
    """Expose configuration discovery without coupling routers to files."""

    def __init__(self, loader: ConfigLoader) -> None:
        self.loader = loader

    def list_all(self) -> dict[str, list[str]]:
        """Return all known config names grouped by category."""

        return {category: self.loader.list_configs(category) for category in sorted(SUPPORTED_CATEGORIES)}

    def list_category(self, category: str) -> list[dict[str, Any]]:
        """Return minimal metadata for every config in a category."""

        configs = []
        for name in self.loader.list_configs(category):
            payload = self.loader.load_json(category, name)
            configs.append({"id": payload.get("id", name), "name": payload.get("name", name), "file": name})
        return configs
