"""Local exported run and replay endpoints."""

from typing import Any

from fastapi import APIRouter

from app.application.run_service import RunService
from app.core.settings import get_settings
from app.infrastructure.exporters import ReplayLoader
from app.schemas.simulation import ReplaySnapshotsResponse, RunSummaryResponse

router = APIRouter(prefix="/runs", tags=["runs"])
service = RunService(ReplayLoader(get_settings().output_directory))


@router.get("", response_model=list[RunSummaryResponse])
def list_runs() -> list[RunSummaryResponse]:
    return service.list_runs()


@router.get("/{run_id}/metadata", response_model=dict[str, Any])
def run_metadata(run_id: str) -> dict[str, object]:
    return service.metadata(run_id)


@router.get("/{run_id}/snapshots", response_model=ReplaySnapshotsResponse)
def run_snapshots(run_id: str) -> ReplaySnapshotsResponse:
    return service.snapshots(run_id)
