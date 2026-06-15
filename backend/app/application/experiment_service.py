"""Deterministic headless batch experiment use cases."""

from statistics import fmean
from typing import Any

from app.core.errors import ExperimentNotFoundError
from app.domain.behavior_params import BehaviorParameters
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.infrastructure.file_storage import FileStorage
from app.schemas.configs import ExperimentConfig, PolicyConfig
from app.schemas.experiments import ExperimentResultResponse
from app.simulation.engine import SimulationEngine


class ExperimentService:
    """Run config-driven policy/behavior/adaptive variants with shared seeds."""

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
        variant_results, run_index, seeds = self.run_variants(experiment)
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

    def run_variants(
        self,
        experiment: ExperimentConfig,
        behavior_overrides: dict[str, float] | None = None,
        ticks: int | None = None,
        seeds: list[int] | None = None,
        population_size: int | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[int]]:
        """Run every variant; reusable by the report runner and the sweep runner.

        ``behavior_overrides`` lets the sweep runner override behavior strengths
        on top of each variant's behavior config.
        """

        scenario = self.loader.load_scenario(experiment.scenario_config)
        disease_config = self.loader.load_disease(experiment.disease_config)
        population = self.loader.load_population(experiment.population_config)
        if population_size is not None:
            population = population.model_copy(update={"population_size": population_size})
        resolved_ticks = ticks if ticks is not None else experiment.ticks
        resolved_seeds = seeds or self._seeds(experiment.seeds, experiment.repetitions)

        variant_results: list[dict[str, Any]] = []
        run_index: list[dict[str, Any]] = []
        for variant in experiment.variants:
            policy_names = variant.policy_configs or (
                [variant.policy_config] if variant.policy_config else []
            )
            policy_configs = [self.loader.load_policy(name) for name in policy_names]
            if policy_configs and variant.overrides:
                policy_payload = {**policy_configs[0].model_dump(), **variant.overrides}
                policy_configs[0] = PolicyConfig.model_validate(policy_payload)
            policies = [self.loader.to_policy(policy) for policy in policy_configs]
            information_events = [
                self.loader.to_information_event(self.loader.load_information(name))
                for name in variant.information_configs
            ]
            behavior_params = self._behavior_params(experiment, variant, behavior_overrides)
            adaptive_policy = (
                self.loader.to_adaptive_policy(
                    self.loader.load_adaptive(variant.adaptive_policy_config)
                )
                if variant.adaptive_policy_config
                else None
            )

            runs = []
            for run_number, seed in enumerate(resolved_seeds):
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
                    information_events=information_events,
                    behavior_params=behavior_params,
                    adaptive_policy=adaptive_policy,
                    config_summary={
                        "experiment_id": experiment.id,
                        "variant_id": variant.id,
                        "seed": seed,
                    },
                )
                snapshot = engine.run(resolved_ticks)
                metrics = self._collect_metrics(engine, snapshot)
                runs.append(
                    {"run_id": run_id, "variant_id": variant.id, "seed": seed, "metrics": metrics}
                )
                run_index.append({"run_id": run_id, "variant_id": variant.id, "seed": seed})

            metric_names = list(runs[0]["metrics"])
            aggregate = {
                name: round(fmean(run["metrics"][name] for run in runs), 6)
                for name in metric_names
            }
            variant_results.append(
                {"variant_id": variant.id, "runs": runs, "aggregate": aggregate}
            )
        return variant_results, run_index, resolved_seeds

    @staticmethod
    def _collect_metrics(engine: SimulationEngine, snapshot: Any) -> dict[str, float]:
        peak = max(engine.state.metrics_history, key=lambda item: item.active_infections)
        history = engine.state.metrics_history[1:] or engine.state.metrics_history
        mean = lambda attr: round(fmean(getattr(item, attr) for item in history), 6)
        return {
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
            "mean_perceived_risk": mean("mean_perceived_risk"),
            "mean_alert_exposure": mean("mean_alert_exposure"),
            "mean_contacts": mean("mean_contacts"),
            "mean_movement_reduction": mean("movement_reduction_estimate"),
            "mean_contact_reduction": mean("contact_reduction_estimate"),
            "mean_real_risk": mean("mean_real_risk"),
            "mean_perception_gap": mean("mean_perception_gap"),
            "mean_trust_authority": mean("mean_trust_authority"),
            "mean_fatigue": mean("mean_fatigue"),
            "mean_compliance": mean("mean_compliance"),
            "mean_rumor_exposure": mean("mean_rumor_exposure"),
            "mean_protection_behavior": mean("mean_protection_behavior"),
            "mean_distancing_behavior": mean("mean_distancing_behavior"),
            "mean_risk_compensation": mean("mean_risk_compensation"),
            "effective_contact_count": mean("effective_contact_count"),
            "effective_beta_mean": mean("effective_beta_mean"),
            "behavioral_transmission_reduction": mean("behavioral_transmission_reduction"),
            "misinformation_transmission_amplification": mean(
                "misinformation_transmission_amplification"
            ),
            "adaptive_policy_trigger_count": snapshot.metrics.adaptive_policy_trigger_count,
        }

    def _behavior_params(
        self,
        experiment: ExperimentConfig,
        variant: Any,
        behavior_overrides: dict[str, float] | None,
    ) -> BehaviorParameters:
        config_name = variant.behavior_config or experiment.behavior_config
        if config_name:
            base = self.loader.load_behavior(config_name).model_dump()
        else:
            base = {}
        defaults = BehaviorParameters()
        fields = {f for f in defaults.__slots__}
        values = {field: base.get(field, getattr(defaults, field)) for field in fields}
        if behavior_overrides:
            values.update({k: v for k, v in behavior_overrides.items() if k in fields})
        return BehaviorParameters(**values)

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
