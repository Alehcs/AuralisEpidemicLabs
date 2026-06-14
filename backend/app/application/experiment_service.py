"""Deterministic headless batch experiment use cases."""

from statistics import fmean

from app.core.errors import ExperimentNotFoundError
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.infrastructure.file_storage import FileStorage
from app.schemas.configs import PolicyConfig
from app.schemas.experiments import ExperimentResultResponse
from app.simulation.engine import SimulationEngine


class ExperimentService:
    """Run config-driven policy variants with shared seeds and fixed ticks."""

    def __init__(
        self,
        loader: ConfigLoader,
        exporter: ExperimentReportExporter,
        output_directory: str,
    ) -> None:
        self.loader = loader
        self.exporter = exporter
        self.storage = FileStorage(output_directory)

    def run(self, experiment_name: str) -> ExperimentResultResponse:
        experiment = self.loader.load_experiment(experiment_name)
        scenario = self.loader.load_scenario(experiment.scenario_config)
        disease_config = self.loader.load_disease(experiment.disease_config)
        population = self.loader.load_population(experiment.population_config)
        seeds = self._seeds(experiment.seeds, experiment.repetitions)
        variant_results = []
        run_index = []

        for variant in experiment.variants:
            policy_names = variant.policy_configs or (
                [variant.policy_config] if variant.policy_config else []
            )
            policy_configs = [self.loader.load_policy(name) for name in policy_names]
            if policy_configs and variant.overrides:
                policy_payload = {**policy_configs[0].model_dump(), **variant.overrides}
                policy_configs[0] = PolicyConfig.model_validate(policy_payload)
            policies = [self.loader.to_policy(policy) for policy in policy_configs]
            runs = []
            for run_number, seed in enumerate(seeds):
                run_id = f"{experiment.id}-{variant.id}-{run_number:02d}-{seed}"
                engine = SimulationEngine.create(
                    simulation_id=run_id,
                    world=self.loader.to_world(scenario),
                    disease=self.loader.to_disease(disease_config),
                    population_config=population,
                    outbreak=scenario.initial_outbreak,
                    seed=seed,
                    policy=policies[0] if len(policies) == 1 else None,
                    policies=policies,
                    config_summary={
                        "experiment_id": experiment.id,
                        "variant_id": variant.id,
                        "seed": seed,
                    },
                )
                snapshot = engine.run(experiment.ticks)
                peak = max(engine.state.metrics_history, key=lambda item: item.active_infections)
                history = engine.state.metrics_history[1:] or engine.state.metrics_history
                metrics = {
                    "final_susceptible": snapshot.metrics.susceptible_count,
                    "final_exposed": snapshot.metrics.exposed_count,
                    "final_infected": (
                        snapshot.metrics.infected_asymptomatic_count
                        + snapshot.metrics.infected_symptomatic_count
                        + snapshot.metrics.isolated_count
                    ),
                    "final_recovered": snapshot.metrics.recovered_count,
                    "cumulative_infections": snapshot.metrics.cumulative_infections,
                    "peak_active_infections": peak.active_infections,
                    "tick_of_peak": peak.tick,
                    "mean_perceived_risk": round(
                        fmean(item.mean_perceived_risk for item in history), 6
                    ),
                    "mean_alert_exposure": round(
                        fmean(item.mean_alert_exposure for item in history), 6
                    ),
                    "mean_contacts": round(fmean(item.mean_contacts for item in history), 6),
                    "mean_movement_reduction": round(
                        fmean(item.movement_reduction_estimate for item in history), 6
                    ),
                    "mean_contact_reduction": round(
                        fmean(item.contact_reduction_estimate for item in history), 6
                    ),
                }
                run = {"run_id": run_id, "variant_id": variant.id, "seed": seed, "metrics": metrics}
                runs.append(run)
                run_index.append({"run_id": run_id, "variant_id": variant.id, "seed": seed})

            metric_names = list(runs[0]["metrics"])
            aggregate = {
                name: round(fmean(run["metrics"][name] for run in runs), 6)
                for name in metric_names
            }
            variant_results.append({"variant_id": variant.id, "runs": runs, "aggregate": aggregate})

        summary = {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "ticks": experiment.ticks,
            "seeds": seeds,
            "variant_count": len(variant_results),
            "run_count": len(run_index),
        }
        report = self.exporter.export(experiment.id, summary, variant_results, run_index)
        return ExperimentResultResponse.model_validate(
            {
                "experiment_id": experiment.id,
                "status": "completed",
                "ticks": experiment.ticks,
                "variants": variant_results,
                "report": report,
            }
        )

    def results(self, experiment_id: str) -> ExperimentResultResponse:
        prefix = f"reports/{experiment_id}"
        summary_path = self.storage.resolve(f"{prefix}/experiment_summary.json")
        if not summary_path.is_file():
            raise ExperimentNotFoundError(f"Experiment results not found: {experiment_id}")
        summary = self.storage.read_json(f"{prefix}/experiment_summary.json")
        variants = self.storage.read_json(f"{prefix}/variant_results.json")
        return ExperimentResultResponse.model_validate(
            {
                "experiment_id": experiment_id,
                "status": "completed",
                "ticks": summary["ticks"],
                "variants": variants,
                "report": {
                    "experiment_id": experiment_id,
                    "directory": str(self.storage.resolve(prefix)),
                    "files": ["experiment_summary.json", "variant_results.json", "run_index.json"],
                },
            }
        )

    @staticmethod
    def _seeds(configured: list[int], repetitions: int) -> list[int]:
        return [configured[index % len(configured)] + index // len(configured) for index in range(repetitions)]
