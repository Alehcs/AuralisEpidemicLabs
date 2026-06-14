"""Exported run discovery and replay use cases."""

from app.infrastructure.exporters import ReplayLoader
from app.schemas.simulation import ReplaySnapshotsResponse, RunSummaryResponse


class RunService:
    """Expose local exported runs without leaking filesystem behavior to API."""

    def __init__(self, replay_loader: ReplayLoader) -> None:
        self.replay_loader = replay_loader

    def list_runs(self) -> list[RunSummaryResponse]:
        return [RunSummaryResponse.model_validate(item) for item in self.replay_loader.list_runs()]

    def metadata(self, run_id: str) -> dict[str, object]:
        return self.replay_loader.metadata(run_id)

    def snapshots(self, run_id: str) -> ReplaySnapshotsResponse:
        return ReplaySnapshotsResponse(
            run_id=run_id,
            snapshots=self.replay_loader.snapshots(run_id),
        )
