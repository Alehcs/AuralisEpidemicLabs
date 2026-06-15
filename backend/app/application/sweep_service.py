"""Deterministic behavior-parameter sensitivity sweep runner.

Runs a chosen experiment over a small cartesian grid of behavior-strength
overrides and reports how the epidemic responds. Intentionally small and
efficient (no optimization or learning); the grid order is deterministic, so the
same sweep config reproduces identical results.
"""

import itertools
from typing import Any

from app.core.errors import ExperimentNotFoundError
from app.application.experiment_service import ExperimentService
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.file_storage import FileStorage
from app.schemas.experiments import SweepResultResponse

FOCUS_METRICS = (
    "cumulative_infections",
    "peak_active_infections",
    "effective_beta_mean",
    "mean_protection_behavior",
    "mean_risk_compensation",
    "misinformation_transmission_amplification",
    "behavioral_transmission_reduction",
    "adaptive_policy_trigger_count",
)
SWEEP_FILES = (
    "sweep_summary.json",
    "parameter_grid.json",
    "run_index.json",
    "variant_results.json",
    "best_response_summary.json",
)


class SweepService:
    """Execute a parameter grid and persist a calibration/sensitivity report."""

    def __init__(
        self,
        loader: ConfigLoader,
        experiment_service: ExperimentService,
        output_directory: str,
    ) -> None:
        self.loader = loader
        self.experiment_service = experiment_service
        self.storage = FileStorage(output_directory)

    def run(self, sweep_name: str) -> SweepResultResponse:
        sweep = self.loader.load_sweep(sweep_name)
        experiment = self.loader.load_experiment(sweep.experiment_config)
        focus_variant = sweep.focus_variant or experiment.variants[-1].id

        grid_points = self._expand_grid(sweep.parameter_grid)
        points: list[dict[str, Any]] = []
        run_index: list[dict[str, Any]] = []
        for index, parameters in enumerate(grid_points):
            variant_results, variant_run_index, _ = self.experiment_service.run_variants(
                experiment,
                behavior_overrides=parameters,
                ticks=sweep.ticks,
                seeds=sweep.seeds,
                population_size=sweep.population_size,
            )
            focus = self._focus_metrics(variant_results, focus_variant)
            points.append(
                {
                    "point_index": index,
                    "parameters": parameters,
                    "variants": [
                        {"variant_id": item["variant_id"], "aggregate": item["aggregate"]}
                        for item in variant_results
                    ],
                    "focus_metrics": focus,
                }
            )
            for entry in variant_run_index:
                run_index.append({"point_index": index, "parameters": parameters, **entry})

        best = min(points, key=lambda item: item["focus_metrics"]["cumulative_infections"])
        best_response = {
            "point_index": best["point_index"],
            "parameters": best["parameters"],
            "focus_variant": focus_variant,
            "focus_metrics": best["focus_metrics"],
        }
        summary = {
            "sweep_id": sweep.id,
            "name": sweep.name,
            "experiment_config": sweep.experiment_config,
            "focus_variant": focus_variant,
            "point_count": len(points),
            "ticks": sweep.ticks if sweep.ticks is not None else experiment.ticks,
            "seeds": sweep.seeds,
            "population_size": sweep.population_size,
            "focus_metrics": list(FOCUS_METRICS),
        }
        report = self._write_report(
            sweep.id, summary, sweep.parameter_grid, run_index, points, best_response
        )
        return SweepResultResponse.model_validate(
            {
                "sweep_id": sweep.id,
                "status": "completed",
                "experiment_config": sweep.experiment_config,
                "parameter_grid": sweep.parameter_grid,
                "focus_variant": focus_variant,
                "points": points,
                "best_response": best_response,
                "report": report,
            }
        )

    def results(self, sweep_id: str) -> SweepResultResponse:
        prefix = f"reports/{sweep_id}"
        summary_path = self.storage.resolve(f"{prefix}/sweep_summary.json")
        if not summary_path.is_file():
            raise ExperimentNotFoundError(f"Sweep results not found: {sweep_id}")
        summary = self.storage.read_json(f"{prefix}/sweep_summary.json")
        grid = self.storage.read_json(f"{prefix}/parameter_grid.json")
        points = self.storage.read_json(f"{prefix}/variant_results.json")
        best = self.storage.read_json(f"{prefix}/best_response_summary.json")
        return SweepResultResponse.model_validate(
            {
                "sweep_id": sweep_id,
                "status": "completed",
                "experiment_config": summary["experiment_config"],
                "parameter_grid": grid["parameter_grid"],
                "focus_variant": summary["focus_variant"],
                "points": points,
                "best_response": best,
                "report": {
                    "sweep_id": sweep_id,
                    "directory": str(self.storage.resolve(prefix)),
                    "files": list(SWEEP_FILES),
                },
            }
        )

    @staticmethod
    def _expand_grid(parameter_grid: dict[str, list[float]]) -> list[dict[str, float]]:
        names = list(parameter_grid.keys())
        combinations = itertools.product(*(parameter_grid[name] for name in names))
        return [dict(zip(names, combo)) for combo in combinations]

    @staticmethod
    def _focus_metrics(
        variant_results: list[dict[str, Any]],
        focus_variant: str,
    ) -> dict[str, float]:
        aggregate = next(
            (
                item["aggregate"]
                for item in variant_results
                if item["variant_id"] == focus_variant
            ),
            variant_results[-1]["aggregate"],
        )
        return {metric: aggregate.get(metric, 0.0) for metric in FOCUS_METRICS}

    def _write_report(
        self,
        sweep_id: str,
        summary: dict[str, Any],
        parameter_grid: dict[str, list[float]],
        run_index: list[dict[str, Any]],
        points: list[dict[str, Any]],
        best_response: dict[str, Any],
    ) -> dict[str, Any]:
        prefix = f"reports/{sweep_id}"
        self.storage.write_json(f"{prefix}/sweep_summary.json", summary)
        self.storage.write_json(
            f"{prefix}/parameter_grid.json",
            {"parameter_grid": parameter_grid, "point_count": len(points)},
        )
        self.storage.write_json(f"{prefix}/run_index.json", run_index)
        self.storage.write_json(f"{prefix}/variant_results.json", points)
        self.storage.write_json(f"{prefix}/best_response_summary.json", best_response)
        return {
            "sweep_id": sweep_id,
            "directory": str(self.storage.resolve(prefix)),
            "files": list(SWEEP_FILES),
        }
