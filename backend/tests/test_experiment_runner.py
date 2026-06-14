"""First deterministic batch experiment report test."""

import json
from pathlib import Path

from app.application.experiment_service import ExperimentService
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter


def test_batch_runner_writes_summary_files(
    config_loader: ConfigLoader,
    tmp_path: Path,
) -> None:
    experiment = config_loader.load_experiment("global_vs_local_alert")
    original_population = config_loader.load_population("default_population_v1")

    config_root = tmp_path / "configs"
    for category in ("scenarios", "diseases", "policies", "populations", "experiments"):
        (config_root / category).mkdir(parents=True)
    source_root = config_loader.base_directory
    config_references = [
        ("scenarios", experiment.scenario_config),
        ("diseases", experiment.disease_config),
    ]
    policy_names = {
        name
        for variant in experiment.variants
        for name in (variant.policy_configs or ([variant.policy_config] if variant.policy_config else []))
    }
    config_references.extend(("policies", name) for name in sorted(policy_names))
    for category, name in config_references:
        (config_root / category / f"{name}.json").write_text(
            (source_root / category / f"{name}.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    population_payload = original_population.model_dump(mode="json")
    population_payload["population_size"] = 120
    (config_root / "populations" / "default_population_v1.json").write_text(
        json.dumps(population_payload),
        encoding="utf-8",
    )
    experiment_payload = experiment.model_dump(mode="json")
    experiment_payload.update({"repetitions": 1, "seeds": [9], "ticks": 36})
    (config_root / "experiments" / "global_vs_local_alert.json").write_text(
        json.dumps(experiment_payload),
        encoding="utf-8",
    )

    output_root = tmp_path / "outputs"
    service = ExperimentService(
        ConfigLoader(config_root),
        ExperimentReportExporter(output_root),
        str(output_root),
    )
    result = service.run("global_vs_local_alert")

    report_directory = output_root / "reports" / "global_vs_local_alert"
    assert result.status == "completed"
    assert len(result.variants) == 4
    assert (report_directory / "experiment_summary.json").is_file()
    assert (report_directory / "variant_results.json").is_file()
    assert (report_directory / "run_index.json").is_file()
    assert service.results("global_vs_local_alert").variants

    aggregates = {variant.variant_id: variant.aggregate for variant in result.variants}
    assert aggregates["baseline_no_policy"]["mean_alert_exposure"] == 0
    assert aggregates["global_alert"]["mean_alert_exposure"] > 0
    assert aggregates["local_alert_market"]["mean_contact_reduction"] > 0
