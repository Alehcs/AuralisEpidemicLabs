"""Deterministic local exporters and replay readers."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.errors import RunNotFoundError
from app.domain.simulation import SimulationState
from app.infrastructure.file_storage import FileStorage

RUN_FILES = (
    "metadata.json",
    "config_summary.json",
    "metrics_history.json",
    "snapshots.jsonl",
    "final_summary.json",
)


class RunExporter:
    """Write one compact, reproducible run bundle under `outputs/runs`."""

    def __init__(self, output_directory: Path | str) -> None:
        self.storage = FileStorage(output_directory)

    def export(self, state: SimulationState) -> dict[str, Any]:
        run_id = state.simulation_id
        prefix = f"runs/{run_id}"
        logical_time = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            minutes=state.tick * state.disease.tick_minutes
        )
        metadata = {
            "run_id": run_id,
            "simulation_id": state.simulation_id,
            "seed": state.seed,
            "tick": state.tick,
            "tick_minutes": state.disease.tick_minutes,
            "exported_at": logical_time.isoformat(),
            "format_version": 1,
        }
        metrics = [asdict(item) for item in state.metrics_history]
        final_metrics = metrics[-1]
        final_summary = {
            "run_id": run_id,
            "tick": state.tick,
            "final_metrics": final_metrics,
            "active_policies": state.active_policy_ids,
        }
        self.storage.write_json(f"{prefix}/metadata.json", metadata)
        self.storage.write_json(f"{prefix}/config_summary.json", state.config_summary)
        self.storage.write_json(f"{prefix}/metrics_history.json", metrics)
        self.storage.write_jsonl(f"{prefix}/snapshots.jsonl", state.snapshots_history)
        self.storage.write_json(f"{prefix}/final_summary.json", final_summary)
        return {
            "run_id": run_id,
            "directory": str(self.storage.resolve(prefix)),
            "files": list(RUN_FILES),
        }


class ReplayLoader:
    """Read metadata and compact snapshots from exported local runs."""

    def __init__(self, output_directory: Path | str) -> None:
        self.storage = FileStorage(output_directory)

    def list_runs(self) -> list[dict[str, Any]]:
        runs_directory = self.storage.resolve("runs")
        if not runs_directory.exists():
            return []
        summaries = []
        for directory in sorted(path for path in runs_directory.iterdir() if path.is_dir()):
            metadata_path = directory / "metadata.json"
            if metadata_path.is_file():
                summaries.append(self.storage.read_json(f"runs/{directory.name}/metadata.json"))
        return summaries

    def metadata(self, run_id: str) -> dict[str, Any]:
        return self._read(run_id, "metadata.json")

    def snapshots(self, run_id: str) -> list[dict[str, Any]]:
        path = self.storage.resolve(f"runs/{run_id}/snapshots.jsonl")
        if not path.is_file():
            raise RunNotFoundError(f"Run not found: {run_id}")
        return self.storage.read_jsonl(f"runs/{run_id}/snapshots.jsonl")

    def _read(self, run_id: str, filename: str) -> dict[str, Any]:
        path = self.storage.resolve(f"runs/{run_id}/{filename}")
        if not path.is_file():
            raise RunNotFoundError(f"Run not found: {run_id}")
        payload = self.storage.read_json(f"runs/{run_id}/{filename}")
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object in {path}")
        return payload


class ExperimentReportExporter:
    """Write deterministic batch comparison reports."""

    def __init__(self, output_directory: Path | str) -> None:
        self.storage = FileStorage(output_directory)

    def export(
        self,
        experiment_id: str,
        summary: dict[str, Any],
        variant_results: list[dict[str, Any]],
        run_index: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prefix = f"reports/{experiment_id}"
        self.storage.write_json(f"{prefix}/experiment_summary.json", summary)
        self.storage.write_json(f"{prefix}/variant_results.json", variant_results)
        self.storage.write_json(f"{prefix}/run_index.json", run_index)
        return {
            "experiment_id": experiment_id,
            "directory": str(self.storage.resolve(prefix)),
            "files": ["experiment_summary.json", "variant_results.json", "run_index.json"],
        }
