"""Service health endpoint."""

from fastapi import APIRouter

from app.core.settings import get_settings
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report liveness and build identity."""

    settings = get_settings()
    return HealthResponse(project=settings.project_name, version=settings.version)
