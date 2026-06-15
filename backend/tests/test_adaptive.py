"""Phase 6 adaptive intervention and calibration-sweep tests."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.application.experiment_service import ExperimentService
from app.application.sweep_service import SweepService
from app.domain.adaptive import (
    ActiveIntervention,
    AdaptiveAction,
    AdaptivePolicy,
    AdaptiveRule,
)
from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.behavior_params import BehaviorParameters
from app.domain.policy import Policy
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.main import app
from app.simulation.adaptive import AdaptivePolicyEngine
from app.simulation.engine import SimulationEngine


def build_engine(
    config_loader: ConfigLoader,
    policies: list[Policy] | None = None,
    behavior_params: BehaviorParameters | None = None,
    adaptive_policy: AdaptivePolicy | None = None,
    seed: int = 42,
    simulation_id: str = "adaptive-test",
) -> SimulationEngine:
    scenario = config_loader.load_scenario("district_v1_market_outbreak")
    disease = config_loader.load_disease("respiratory_like_v1")
    population = config_loader.load_population("default_population_v1")
    return SimulationEngine.create(
        simulation_id=simulation_id,
        world=config_loader.to_world(scenario),
        disease=config_loader.to_disease(disease),
        population_config=population,
        outbreak=scenario.initial_outbreak,
        seed=seed,
        policies=policies or [],
        behavior_params=behavior_params,
        adaptive_policy=adaptive_policy,
    )


def make_agent(agent_id: str, zone_id: str, **changes: object) -> Agent:
    agent = Agent(
        id=agent_id,
        profile="obedient",
        zone_id=zone_id,
        home_zone_id=zone_id,
        work_zone_id=None,
        school_zone_id=None,
        routine_type=RoutineType.UNEMPLOYED,
        movement_tendency=0.8,
    )
    for key, value in changes.items():
        setattr(agent, key, value)
    return agent


def rule(**changes: object) -> AdaptiveRule:
    base = {
        "id": "r1",
        "metric": "misinformation_transmission_amplification",
        "operator": ">",
        "threshold": 0.1,
        "action": AdaptiveAction.COUNTER_MESSAGING,
        "duration_ticks": 10,
        "intensity": 0.7,
        "cooldown_ticks": 10,
    }
    base.update(changes)
    return AdaptiveRule(**base)


def test_behavior_defaults_preserve_old_behavior(config_loader: ConfigLoader) -> None:
    default = build_engine(config_loader, seed=55, simulation_id="b")
    explicit = build_engine(
        config_loader,
        behavior_params=BehaviorParameters(),
        seed=55,
        simulation_id="b",
    )
    default.run(20)
    explicit.run(20)

    signature = lambda engine: [
        (
            item.effective_beta_mean,
            item.behavioral_transmission_reduction,
            item.misinformation_transmission_amplification,
        )
        for item in engine.state.metrics_history
    ]
    assert signature(default) == signature(explicit)


def test_behavior_constants_overridden_by_config(config_loader: ConfigLoader) -> None:
    strong = BehaviorParameters(susceptible_protection_strength=2.0)
    baseline = build_engine(config_loader, seed=7, simulation_id="x")
    treated = build_engine(config_loader, behavior_params=strong, seed=7, simulation_id="x")

    baseline.run(40)
    treated.run(40)

    # Stronger susceptible protection lowers the effective transmission coefficient.
    assert (
        treated.state.metrics_history[-1].effective_beta_mean
        < baseline.state.metrics_history[-1].effective_beta_mean
    )


def test_adaptive_rule_triggers_when_metric_crosses_threshold() -> None:
    engine = AdaptivePolicyEngine()
    policy = AdaptivePolicy(id="p", rules=(rule(threshold=0.1),))

    below = engine.evaluate(policy, {"misinformation_transmission_amplification": 0.05}, {}, tick=1)
    assert below == []
    above = engine.evaluate(policy, {"misinformation_transmission_amplification": 0.2}, {}, tick=2)
    assert len(above) == 1
    assert engine.trigger_count == 1
    assert engine.last_triggered_rule == "r1"


def test_adaptive_rule_respects_cooldown() -> None:
    engine = AdaptivePolicyEngine()
    policy = AdaptivePolicy(
        id="p", rules=(rule(threshold=0.1, duration_ticks=2, cooldown_ticks=20),)
    )
    context = {"misinformation_transmission_amplification": 0.5}

    engine.evaluate(policy, context, {}, tick=1)
    assert engine.trigger_count == 1
    # Expires at tick 3; re-firing at tick 5 is still inside the 20-tick cooldown.
    engine.evaluate(policy, context, {}, tick=5)
    assert engine.trigger_count == 1
    # After cooldown elapses it can trigger again.
    engine.evaluate(policy, context, {}, tick=22)
    assert engine.trigger_count == 2


def test_counter_messaging_reduces_false_safety_exposure() -> None:
    engine = AdaptivePolicyEngine()
    engine.active = [
        ActiveIntervention(
            rule_id="r1",
            action=AdaptiveAction.COUNTER_MESSAGING,
            target="global",
            target_zone_id=None,
            intensity=0.8,
            start_tick=1,
            end_tick=20,
        )
    ]
    agent = make_agent("a", "market", safety_rumor_exposure=0.8, rumor_belief=0.6)

    engine.apply([agent], tick=2)

    assert agent.safety_rumor_exposure < 0.8
    assert agent.rumor_belief < 0.6


def test_peer_warning_campaign_increases_peer_warning_exposure() -> None:
    engine = AdaptivePolicyEngine()
    engine.active = [
        ActiveIntervention(
            rule_id="r2",
            action=AdaptiveAction.PEER_WARNING_CAMPAIGN,
            target="global",
            target_zone_id=None,
            intensity=0.9,
            start_tick=1,
            end_tick=20,
        )
    ]
    agent = make_agent("a", "market", peer_warning_exposure=0.0, trust_peers=0.4)

    engine.apply([agent], tick=2)

    assert agent.peer_warning_exposure > 0.0
    assert agent.trust_peers > 0.4


def test_adaptive_isolation_increases_isolation_among_symptomatic() -> None:
    engine = AdaptivePolicyEngine()
    engine.active = [
        ActiveIntervention(
            rule_id="r3",
            action=AdaptiveAction.ADAPTIVE_ISOLATION_ENCOURAGEMENT,
            target="global",
            target_zone_id=None,
            intensity=0.9,
            start_tick=1,
            end_tick=20,
        )
    ]
    symptomatic = make_agent(
        "sym", "market", isolation_compliance=0.5, state=EpidemiologicalState.INFECTED_SYMPTOMATIC
    )

    isolated = engine.apply_adaptive_isolation([symptomatic], tick=2)

    assert isolated == 1
    assert symptomatic.state == EpidemiologicalState.ISOLATED


def test_adaptive_counter_message_reduces_infections_vs_static(
    config_loader: ConfigLoader,
) -> None:
    safety = replace(
        config_loader.to_information_event(config_loader.load_information("false_safety_market")),
        start_tick=1,
    )
    adaptive = config_loader.to_adaptive_policy(
        config_loader.load_adaptive("adaptive_counter_misinformation_v1")
    )

    def cumulative(adaptive_policy: AdaptivePolicy | None) -> int:
        total = 0
        for seed in (42, 84):
            engine = SimulationEngine.create(
                simulation_id="cmp",
                world=config_loader.to_world(
                    config_loader.load_scenario("district_v1_market_outbreak")
                ),
                disease=config_loader.to_disease(
                    config_loader.load_disease("respiratory_like_v1")
                ),
                population_config=config_loader.load_population("default_population_v1"),
                outbreak=config_loader.load_scenario(
                    "district_v1_market_outbreak"
                ).initial_outbreak,
                seed=seed,
                information_events=[safety],
                adaptive_policy=adaptive_policy,
            )
            engine.run(120)
            total += engine.state.cumulative_infections
        return total

    no_response = cumulative(None)
    adaptive_response = cumulative(adaptive)
    assert adaptive_response < no_response


def test_static_vs_adaptive_experiment_writes_summary(
    config_loader: ConfigLoader,
    tmp_path: Path,
) -> None:
    experiment = config_loader.load_experiment("static_vs_adaptive_policy")
    population = config_loader.load_population("default_population_v1")
    source_root = config_loader.base_directory

    config_root = tmp_path / "configs"
    for category in (
        "scenarios",
        "diseases",
        "policies",
        "populations",
        "experiments",
        "information",
        "behavior",
        "adaptive",
    ):
        (config_root / category).mkdir(parents=True)
    references = [
        ("scenarios", experiment.scenario_config),
        ("diseases", experiment.disease_config),
        ("policies", "local_alert_policy"),
        ("policies", "global_alert_policy"),
        ("information", "false_safety_market"),
        ("information", "anti_authority_rumor"),
        ("behavior", "responsive_population_v1"),
        ("adaptive", "adaptive_counter_misinformation_v1"),
        ("adaptive", "adaptive_peer_warning_v1"),
    ]
    for category, name in references:
        (config_root / category / f"{name}.json").write_text(
            (source_root / category / f"{name}.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    population_payload = population.model_dump(mode="json")
    population_payload["population_size"] = 150
    (config_root / "populations" / "default_population_v1.json").write_text(
        json.dumps(population_payload), encoding="utf-8"
    )
    experiment_payload = experiment.model_dump(mode="json")
    experiment_payload.update({"repetitions": 1, "seeds": [9], "ticks": 48})
    (config_root / "experiments" / "static_vs_adaptive_policy.json").write_text(
        json.dumps(experiment_payload), encoding="utf-8"
    )

    output_root = tmp_path / "outputs"
    service = ExperimentService(
        ConfigLoader(config_root),
        ExperimentReportExporter(output_root),
        str(output_root),
    )
    result = service.run("static_vs_adaptive_policy")

    report_directory = output_root / "reports" / "static_vs_adaptive_policy"
    assert result.status == "completed"
    assert len(result.variants) == 5
    assert (report_directory / "experiment_summary.json").is_file()
    aggregates = {variant.variant_id: variant.aggregate for variant in result.variants}
    assert "adaptive_policy_trigger_count" in aggregates["baseline"]
    assert (
        aggregates["false_safety_adaptive_counter_message"]["adaptive_policy_trigger_count"]
        > 0
    )


def test_sweep_runner_writes_files_and_is_deterministic(
    config_loader: ConfigLoader,
    tmp_path: Path,
) -> None:
    sweep = config_loader.load_sweep("behavior_sensitivity_v1")
    experiment = config_loader.load_experiment(sweep.experiment_config)
    population = config_loader.load_population("default_population_v1")
    source_root = config_loader.base_directory

    config_root = tmp_path / "configs"
    for category in (
        "scenarios",
        "diseases",
        "policies",
        "populations",
        "experiments",
        "information",
        "sweeps",
    ):
        (config_root / category).mkdir(parents=True)
    references = [
        ("scenarios", experiment.scenario_config),
        ("diseases", experiment.disease_config),
        ("policies", "local_alert_policy"),
        ("policies", "global_alert_policy"),
        ("information", "false_safety_market"),
        ("information", "anti_authority_rumor"),
        ("information", "panic_rumor_district"),
    ]
    for category, name in references:
        (config_root / category / f"{name}.json").write_text(
            (source_root / category / f"{name}.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    population_payload = population.model_dump(mode="json")
    (config_root / "populations" / "default_population_v1.json").write_text(
        json.dumps(population_payload), encoding="utf-8"
    )
    experiment_payload = experiment.model_dump(mode="json")
    (config_root / "experiments" / f"{experiment.id}.json").write_text(
        json.dumps(experiment_payload), encoding="utf-8"
    )
    sweep_payload = sweep.model_dump(mode="json")
    sweep_payload.update(
        {
            "parameter_grid": {"risk_compensation_strength": [0.6, 1.5]},
            "ticks": 36,
            "population_size": 120,
            "seeds": [9],
        }
    )
    (config_root / "sweeps" / "behavior_sensitivity_v1.json").write_text(
        json.dumps(sweep_payload), encoding="utf-8"
    )

    output_root = tmp_path / "outputs"
    loader = ConfigLoader(config_root)
    experiment_service = ExperimentService(
        loader, ExperimentReportExporter(output_root), str(output_root)
    )
    sweep_service = SweepService(loader, experiment_service, str(output_root))
    result = sweep_service.run("behavior_sensitivity_v1")

    report_directory = output_root / "reports" / "behavior_sensitivity_v1"
    for filename in (
        "sweep_summary.json",
        "parameter_grid.json",
        "run_index.json",
        "variant_results.json",
        "best_response_summary.json",
    ):
        assert (report_directory / filename).is_file()
    assert len(result.points) == 2

    rerun = sweep_service.run("behavior_sensitivity_v1")
    assert [point.focus_metrics for point in result.points] == [
        point.focus_metrics for point in rerun.points
    ]


def test_api_create_run_and_adaptive_policies_flow() -> None:
    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post(
                "/simulations/create",
                json={
                    "policy_config": None,
                    "policy_configs": [],
                    "information_configs": ["false_safety_market"],
                    "adaptive_policy_config": "adaptive_counter_misinformation_v1",
                    "seed": 21,
                },
            )
            assert created.status_code == 201
            simulation_id = created.json()["simulation_id"]

            ran = await client.post(
                f"/simulations/{simulation_id}/run", json={"ticks": 60}
            )
            assert ran.status_code == 200
            metrics = ran.json()["snapshot"]["metrics"]
            assert "adaptive_policy_trigger_count" in metrics

            adaptive = await client.get(f"/simulations/{simulation_id}/adaptive-policies")
            assert adaptive.status_code == 200
            assert adaptive.json()["policy_id"] == "adaptive_counter_misinformation_v1"
            assert adaptive.json()["trigger_count"] >= 0

            missing = await client.get("/simulations/unknown/adaptive-policies")
            assert missing.status_code == 404

    asyncio.run(exercise())
