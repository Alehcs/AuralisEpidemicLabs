"""Headless experiment execution and result endpoints."""

from fastapi import APIRouter

from app.application.experiment_service import ExperimentService
from app.core.settings import get_settings
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.schemas.experiments import ExperimentResultResponse, ExperimentRunRequest

router = APIRouter(prefix="/experiments", tags=["experiments"])
settings = get_settings()
service = ExperimentService(
    ConfigLoader(settings.config_directory),
    ExperimentReportExporter(settings.output_directory),
    str(settings.output_directory),
)


@router.post("/run", response_model=ExperimentResultResponse)
def run_experiment(request: ExperimentRunRequest) -> ExperimentResultResponse:
    return service.run(request.experiment_config)


@router.get("/{experiment_id}/results", response_model=ExperimentResultResponse)
def experiment_results(experiment_id: str) -> ExperimentResultResponse:
    return service.results(experiment_id)
