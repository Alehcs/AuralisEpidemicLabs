"""Phase 5 behavior-driven transmission and social-propagation tests."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.application.experiment_service import ExperimentService
from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.information import InformationEvent
from app.domain.policy import Policy
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import ExperimentReportExporter
from app.main import app
from app.simulation.behavior import BehaviorEngine
from app.simulation.contacts import ContactEngine
from app.simulation.engine import SimulationEngine
from app.simulation.policies import PolicyModifiers
from app.simulation.social import SocialInfluenceEngine
from app.simulation.transmission import TransmissionEngine


def build_engine(
    config_loader: ConfigLoader,
    policies: list[Policy] | None = None,
    events: list[InformationEvent] | None = None,
    seed: int = 42,
    simulation_id: str = "behavior-test",
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


def test_behavior_fields_initialize_deterministically(config_loader: ConfigLoader) -> None:
    first = build_engine(config_loader, seed=321, simulation_id="b-det")
    second = build_engine(config_loader, seed=321, simulation_id="b-det")

    first.run(12)
    second.run(12)

    signature = lambda engine: [
        (
            round(agent.protection_behavior, 6),
            round(agent.distancing_behavior, 6),
            round(agent.risk_compensation, 6),
            round(agent.risky_optional_movement_bias, 6),
        )
        for agent in engine.state.agents
    ]
    assert signature(first) == signature(second)


def test_high_perceived_risk_increases_protection() -> None:
    worried = make_agent("worried", "market", perceived_risk=0.9, adaptive_compliance=0.6)
    calm = make_agent("calm", "market", perceived_risk=0.0, adaptive_compliance=0.6)
    BehaviorEngine().step([worried, calm], PolicyModifiers(), tick=1)

    assert worried.protection_behavior > calm.protection_behavior
    assert worried.distancing_behavior > calm.distancing_behavior


def test_high_fatigue_reduces_protection() -> None:
    rested = make_agent("rested", "market", perceived_risk=0.6, adaptive_compliance=0.6, fatigue=0.0)
    tired = make_agent("tired", "market", perceived_risk=0.6, adaptive_compliance=0.6, fatigue=0.9)
    BehaviorEngine().step([rested, tired], PolicyModifiers(), tick=1)

    assert tired.protection_behavior < rested.protection_behavior


def test_false_safety_reduces_protection_and_increases_risky_movement() -> None:
    base = make_agent(
        "base", "market", perceived_risk=0.4, adaptive_compliance=0.6, rumor_belief=0.8
    )
    duped = make_agent(
        "duped",
        "market",
        perceived_risk=0.4,
        adaptive_compliance=0.6,
        rumor_belief=0.8,
        safety_rumor_exposure=0.9,
    )
    BehaviorEngine().step([base, duped], PolicyModifiers(), tick=1)

    assert duped.protection_behavior < base.protection_behavior
    assert duped.distancing_behavior < base.distancing_behavior
    assert duped.risky_optional_movement_bias > base.risky_optional_movement_bias


def test_behavior_reduces_effective_contacts(config_loader: ConfigLoader) -> None:
    scenario = config_loader.load_scenario("district_v1_market_outbreak")
    world = config_loader.to_world(scenario)
    careful = [
        make_agent(f"c{i}", "market", distancing_behavior=0.9) for i in range(40)
    ]
    careless = [make_agent(f"n{i}", "market") for i in range(40)]
    engine = ContactEngine()

    careful_batch = engine.step(careful, world, tick=1, tick_minutes=60)
    careless_batch = engine.step(careless, world, tick=1, tick_minutes=60)

    assert careful_batch.effective_contact_count < careless_batch.effective_contact_count
    # Raw mixing is identical; only behavior differs.
    assert careful_batch.raw_contact_count == careless_batch.raw_contact_count


def test_behavior_reduces_effective_transmission(config_loader: ConfigLoader) -> None:
    scenario = config_loader.load_scenario("district_v1_market_outbreak")
    world = config_loader.to_world(scenario)
    contacts = ContactEngine()
    transmission = TransmissionEngine()

    def run_zone(protection: float) -> float:
        import random

        agents = [make_agent(f"i{i}", "market") for i in range(5)]
        for agent in agents:
            agent.state = EpidemiologicalState.INFECTED_SYMPTOMATIC
            agent.infectiousness = 1.0
        for i in range(95):
            agents.append(make_agent(f"s{i}", "market", protection_behavior=protection))
        batch = contacts.step(agents, world, tick=1, tick_minutes=60)
        result = transmission.transmit(batch, world, config_loader.to_disease(
            config_loader.load_disease("respiratory_like_v1")
        ), tick=1, rng=random.Random(0))
        return result.effective_beta_mean

    protected_beta = run_zone(0.9)
    unprotected_beta = run_zone(0.0)
    assert protected_beta < unprotected_beta


def test_rumor_pressure_spreads_peer_rumor_exposure() -> None:
    believers = [
        make_agent(f"b{i}", "market", safety_rumor_exposure=0.9, rumor_belief=0.9)
        for i in range(5)
    ]
    target = make_agent("target", "market", skepticism=0.0)
    SocialInfluenceEngine().step(believers + [target], ("market",), tick=1)

    assert target.peer_rumor_exposure > 0.0


def test_anti_authority_pressure_reduces_trust_authority() -> None:
    spreaders = [
        make_agent(f"a{i}", "market", anti_authority_exposure=0.9, rumor_belief=0.9)
        for i in range(5)
    ]
    target = make_agent("target", "market", trust_authority=0.6, rumor_belief=0.6, skepticism=0.0)
    SocialInfluenceEngine().step(spreaders + [target], ("market",), tick=1)

    assert target.trust_authority < 0.6


def test_same_seed_produces_same_behavior_metrics(config_loader: ConfigLoader) -> None:
    events = [
        config_loader.to_information_event(
            config_loader.load_information("false_safety_market")
        )
    ]
    first = build_engine(config_loader, [], events, seed=606, simulation_id="b-same")
    second = build_engine(config_loader, [], events, seed=606, simulation_id="b-same")

    first.run(30)
    second.run(30)

    behavior = lambda metric: (
        metric.mean_protection_behavior,
        metric.mean_distancing_behavior,
        metric.mean_risk_compensation,
        metric.effective_contact_count,
        metric.effective_beta_mean,
        metric.behavioral_transmission_reduction,
        metric.misinformation_transmission_amplification,
    )
    assert [behavior(item) for item in first.state.metrics_history] == [
        behavior(item) for item in second.state.metrics_history
    ]


def test_misinformation_reduces_alert_effectiveness(config_loader: ConfigLoader) -> None:
    alert = replace(config_loader.to_policy(config_loader.load_policy("local_alert_policy")), start_tick=1)
    rumor = replace(
        config_loader.to_information_event(config_loader.load_information("false_safety_market")),
        start_tick=1,
    )

    def totals(events: list[InformationEvent]) -> tuple[int, float]:
        cumulative = 0
        protection = 0.0
        for seed in (42, 84):
            engine = build_engine(config_loader, [alert], events, seed=seed, simulation_id="m")
            engine.run(120)
            cumulative += engine.state.cumulative_infections
            protection += engine.state.metrics_history[-1].mean_protection_behavior
        return cumulative, protection

    alert_cumulative, alert_protection = totals([])
    rumor_cumulative, rumor_protection = totals([rumor])

    # False safety lowers protection behavior and, averaged across seeds, leaves
    # the epidemic larger than the alert alone would have.
    assert rumor_protection < alert_protection
    assert rumor_cumulative > alert_cumulative


def test_misinformation_epidemic_impact_writes_summaries(
    config_loader: ConfigLoader,
    tmp_path: Path,
) -> None:
    experiment = config_loader.load_experiment("misinformation_epidemic_impact")
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
    population_payload["population_size"] = 150
    (config_root / "populations" / "default_population_v1.json").write_text(
        json.dumps(population_payload), encoding="utf-8"
    )
    experiment_payload = experiment.model_dump(mode="json")
    experiment_payload.update({"repetitions": 1, "seeds": [9], "ticks": 48})
    (config_root / "experiments" / "misinformation_epidemic_impact.json").write_text(
        json.dumps(experiment_payload), encoding="utf-8"
    )

    output_root = tmp_path / "outputs"
    service = ExperimentService(
        ConfigLoader(config_root),
        ExperimentReportExporter(output_root),
        str(output_root),
    )
    result = service.run("misinformation_epidemic_impact")

    report_directory = output_root / "reports" / "misinformation_epidemic_impact"
    assert result.status == "completed"
    assert len(result.variants) == 6
    assert (report_directory / "experiment_summary.json").is_file()
    assert (report_directory / "variant_results.json").is_file()

    aggregates = {variant.variant_id: variant.aggregate for variant in result.variants}
    assert "effective_beta_mean" in aggregates["baseline"]
    assert "behavioral_transmission_reduction" in aggregates["official_local_alert"]
    assert (
        aggregates["false_safety_rumor"]["mean_protection_behavior"]
        < aggregates["official_local_alert"]["mean_protection_behavior"]
    )


def test_api_exposes_behavior_and_social() -> None:
    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post(
                "/simulations/create",
                json={
                    "policy_config": None,
                    "policy_configs": ["local_alert_policy"],
                    "information_configs": ["false_safety_market"],
                    "seed": 13,
                },
            )
            assert created.status_code == 201
            simulation_id = created.json()["simulation_id"]

            ran = await client.post(
                f"/simulations/{simulation_id}/run", json={"ticks": 40}
            )
            assert ran.status_code == 200
            metrics = ran.json()["snapshot"]["metrics"]
            assert "mean_protection_behavior" in metrics
            assert "effective_beta_mean" in metrics
            assert metrics["raw_contact_count"] >= metrics["effective_contact_count"]

            behavior = await client.get(f"/simulations/{simulation_id}/behavior")
            assert behavior.status_code == 200
            assert behavior.json()["metrics"]["effective_beta_mean"] >= 0

            social = await client.get(f"/simulations/{simulation_id}/social")
            assert social.status_code == 200
            assert "market" in social.json()["zone_pressures"]

    asyncio.run(exercise())
