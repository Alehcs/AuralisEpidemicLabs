"""Configuration discovery endpoints."""

from typing import Any

from fastapi import APIRouter

from app.application.config_service import ConfigService
from app.core.settings import get_settings
from app.infrastructure.config_loader import ConfigLoader

router = APIRouter(prefix="/configs", tags=["configs"])
service = ConfigService(ConfigLoader(get_settings().config_directory))


@router.get("")
def list_configs() -> dict[str, list[str]]:
    """List available config files grouped by category."""

    return service.list_all()


@router.get("/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    """List scenario config metadata."""

    return service.list_category("scenarios")


@router.get("/diseases")
def list_diseases() -> list[dict[str, Any]]:
    """List disease config metadata."""

    return service.list_category("diseases")
