"""Phase 4 socio-cognitive, trust, fatigue, memory and rumor tests."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.application.experiment_service import ExperimentService
from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.information import InformationEvent, InformationType
from app.domain.policy import Policy
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.main import app
from app.simulation.cognition import CognitionEngine
from app.simulation.engine import SimulationEngine
from app.simulation.policies import PolicyModifiers


def build_engine(
    config_loader: ConfigLoader,
    policies: list[Policy] | None = None,
    events: list[InformationEvent] | None = None,
    seed: int = 42,
    simulation_id: str = "cognition-test",
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
        information_events=events or [],
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


def policy(config_loader: ConfigLoader, name: str, **changes: object) -> Policy:
    return replace(config_loader.to_policy(config_loader.load_policy(name)), **changes)


def test_cognitive_state_initializes_deterministically(config_loader: ConfigLoader) -> None:
    first = build_engine(config_loader, seed=2024, simulation_id="det")
    second = build_engine(config_loader, seed=2024, simulation_id="det")

    signature = lambda engine: [
        (
            round(agent.trust_authority, 6),
            round(agent.skepticism, 6),
            round(agent.rumor_belief, 6),
            round(agent.adaptive_compliance, 6),
        )
        for agent in engine.state.agents
    ]

    assert signature(first) == signature(second)
    # Bounded and genuinely varied (not all identical).
    values = {agent.trust_authority for agent in first.state.agents}
    assert len(values) > 1
    assert all(0.0 <= agent.trust_authority <= 1.0 for agent in first.state.agents)


def test_fatigue_increases_under_active_global_alert(config_loader: ConfigLoader) -> None:
    alert = policy(config_loader, "global_alert_policy", start_tick=1)
    treated = build_engine(config_loader, [alert], seed=7, simulation_id="fatigue-alert")
    baseline = build_engine(config_loader, [], seed=7, simulation_id="fatigue-base")

    treated.run(24)
    baseline.run(24)

    assert treated.state.metrics_history[-1].mean_fatigue > 0.0
    assert (
        treated.state.metrics_history[-1].mean_fatigue
        > baseline.state.metrics_history[-1].mean_fatigue
    )


def test_fatigue_decreases_during_no_policy_periods(config_loader: ConfigLoader) -> None:
    engine = build_engine(config_loader, [], seed=7, simulation_id="fatigue-recover")
    for agent in engine.state.agents:
        agent.fatigue = 0.8
    before = sum(agent.fatigue for agent in engine.state.agents) / len(engine.state.agents)

    engine.run(6)

    after = engine.state.metrics_history[-1].mean_fatigue
    assert after < before


def test_local_real_risk_increases_perceived_risk() -> None:
    high = make_agent("a-high", "market")
    low = make_agent("a-low", "periphery")
    CognitionEngine().step(
        [high, low],
        {"market": 0.3, "periphery": 0.0},
        PolicyModifiers(),
        tick=1,
    )

    assert high.perceived_risk > low.perceived_risk
    assert high.real_risk == 0.3


def test_false_safety_rumor_lowers_perceived_risk() -> None:
    believer = make_agent(
        "believer",
        "market",
        rumor_belief=0.8,
        skepticism=0.1,
        safety_rumor_exposure=0.8,
        state=EpidemiologicalState.SUSCEPTIBLE,
    )
    control = make_agent(
        "control",
        "market",
        rumor_belief=0.8,
        skepticism=0.1,
        state=EpidemiologicalState.SUSCEPTIBLE,
    )
    CognitionEngine().step([believer, control], {"market": 0.2}, PolicyModifiers(), tick=1)

    assert believer.perceived_risk < control.perceived_risk


def test_anti_authority_rumor_lowers_trust_authority(config_loader: ConfigLoader) -> None:
    rumor = config_loader.to_information_event(
        config_loader.load_information("anti_authority_rumor")
    )
    rumor = replace(rumor, start_tick=1)
    treated = build_engine(config_loader, [], [rumor], seed=5, simulation_id="anti-auth")
    baseline = build_engine(config_loader, [], [], seed=5, simulation_id="anti-base")

    treated.run(20)
    baseline.run(20)

    assert (
        treated.state.metrics_history[-1].mean_trust_authority
        < baseline.state.metrics_history[-1].mean_trust_authority
    )


def test_compliance_decreases_with_high_fatigue() -> None:
    rested = make_agent("rested", "market", fatigue=0.0)
    exhausted = make_agent("exhausted", "market", fatigue=0.9)
    CognitionEngine().step([rested, exhausted], {"market": 0.1}, PolicyModifiers(), tick=1)

    assert exhausted.adaptive_compliance < rested.adaptive_compliance


def test_same_seed_produces_same_cognitive_metrics(config_loader: ConfigLoader) -> None:
    events = [
        config_loader.to_information_event(
            config_loader.load_information("false_safety_market")
        )
    ]
    first = build_engine(config_loader, [], events, seed=909, simulation_id="same")
    second = build_engine(config_loader, [], events, seed=909, simulation_id="same")

    first.run(30)
    second.run(30)

    cognitive = lambda metric: (
        metric.mean_perceived_risk,
        metric.mean_real_risk,
        metric.mean_perception_gap,
        metric.mean_trust_authority,
        metric.mean_fatigue,
        metric.mean_compliance,
        metric.mean_rumor_exposure,
    )
    assert [cognitive(item) for item in first.state.metrics_history] == [
        cognitive(item) for item in second.state.metrics_history
    ]


def test_official_information_and_rumors_are_exposed(config_loader: ConfigLoader) -> None:
    safety = config_loader.to_information_event(
        config_loader.load_information("false_safety_market")
    )
    engine = build_engine(
        config_loader, [], [replace(safety, start_tick=1)], seed=3, simulation_id="info"
    )

    engine.run(10)

    final = engine.state.metrics_history[-1]
    assert final.rumor_exposure_count > 0
    assert final.false_safety_exposure_count > 0
    assert any(agent.rumor_exposure > 0 for agent in engine.state.agents)


def test_rumor_batch_experiment_writes_expected_summaries(
    config_loader: ConfigLoader,
    tmp_path: Path,
) -> None:
    experiment = config_loader.load_experiment("official_alert_vs_rumors")
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
    ):
        (config_root / category).mkdir(parents=True)

    references = [
        ("scenarios", experiment.scenario_config),
        ("diseases", experiment.disease_config),
        ("policies", "local_alert_policy"),
        ("policies", "global_alert_policy"),
        ("information", "false_safety_market"),
        ("information", "anti_authority_rumor"),
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
    (config_root / "experiments" / "official_alert_vs_rumors.json").write_text(
        json.dumps(experiment_payload), encoding="utf-8"
    )

    output_root = tmp_path / "outputs"
    service = ExperimentService(
        ConfigLoader(config_root),
        ExperimentReportExporter(output_root),
        str(output_root),
    )
    result = service.run("official_alert_vs_rumors")

    report_directory = output_root / "reports" / "official_alert_vs_rumors"
    assert result.status == "completed"
    assert len(result.variants) == 6
    assert (report_directory / "experiment_summary.json").is_file()
    assert (report_directory / "variant_results.json").is_file()

    aggregates = {variant.variant_id: variant.aggregate for variant in result.variants}
    assert "mean_perception_gap" in aggregates["baseline"]
    assert aggregates["false_safety_rumor"]["mean_rumor_exposure"] > 0
    assert (
        aggregates["anti_authority_rumor_plus_alert"]["mean_trust_authority"]
        < aggregates["baseline"]["mean_trust_authority"]
    )


def test_api_exposes_cognition_and_information() -> None:
    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post(
                "/simulations/create",
                json={
                    "policy_config": None,
                    "policy_configs": ["global_alert_policy"],
                    "information_configs": ["false_safety_market", "anti_authority_rumor"],
                    "seed": 11,
                },
            )
            assert created.status_code == 201
            simulation_id = created.json()["simulation_id"]

            ran = await client.post(
                f"/simulations/{simulation_id}/run", json={"ticks": 30}
            )
            assert ran.status_code == 200
            metrics = ran.json()["snapshot"]["metrics"]
            assert "mean_trust_authority" in metrics
            assert "mean_perception_gap" in metrics

            cognition = await client.get(f"/simulations/{simulation_id}/cognition")
            assert cognition.status_code == 200
            assert cognition.json()["metrics"]["mean_trust_authority"] >= 0

            information = await client.get(f"/simulations/{simulation_id}/information")
            assert information.status_code == 200
            assert len(information.json()["events"]) == 2
            assert information.json()["exposure"]["rumor_exposure_count"] > 0

    asyncio.run(exercise())
