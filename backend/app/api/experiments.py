"""Headless experiment endpoints."""

from fastapi import APIRouter

from app.application.experiment_service import ExperimentService
from app.schemas.configs import ExperimentConfig
from app.schemas.responses import MessageResponse

router = APIRouter(prefix="/experiments", tags=["experiments"])
service = ExperimentService()


@router.post("/run", response_model=MessageResponse, status_code=202)
def run_experiment(experiment: ExperimentConfig) -> MessageResponse:
    """Validate and acknowledge an experiment definition."""

    return service.run(experiment)
