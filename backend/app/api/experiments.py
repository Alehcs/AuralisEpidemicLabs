"""Headless experiment execution, sweep, and result endpoints."""

from fastapi import APIRouter

from app.application.experiment_service import ExperimentService
from app.application.sweep_service import SweepService
from app.core.settings import get_settings
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.schemas.experiments import (
    ExperimentResultResponse,
    ExperimentRunRequest,
    SweepResultResponse,
    SweepRunRequest,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])
settings = get_settings()
_loader = ConfigLoader(settings.config_directory)
service = ExperimentService(
    _loader,
    ExperimentReportExporter(settings.output_directory),
    str(settings.output_directory),
)
sweep_service = SweepService(_loader, service, str(settings.output_directory))


@router.post("/run", response_model=ExperimentResultResponse)
def run_experiment(request: ExperimentRunRequest) -> ExperimentResultResponse:
    return service.run(request.experiment_config)


@router.post("/sweep", response_model=SweepResultResponse)
def run_sweep(request: SweepRunRequest) -> SweepResultResponse:
    return sweep_service.run(request.sweep_config)


@router.get("/{experiment_id}/results", response_model=ExperimentResultResponse)
def experiment_results(experiment_id: str) -> ExperimentResultResponse:
    return service.results(experiment_id)


@router.get("/{experiment_id}/sweep-results", response_model=SweepResultResponse)
def sweep_results(experiment_id: str) -> SweepResultResponse:
    return sweep_service.results(experiment_id)
