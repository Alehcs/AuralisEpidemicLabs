"""Phase 3 intervention and official-alert behavior tests."""

from dataclasses import asdict, replace

from app.domain.agent import EpidemiologicalState
from app.domain.policy import Policy, PolicyType
from app.infrastructure.config_loader import ConfigLoader
from app.simulation.engine import SimulationEngine
from app.simulation.information import InformationEngine


def build_engine(
    config_loader: ConfigLoader,
    policies: list[Policy],
    seed: int = 42,
    simulation_id: str = "policy-test",
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
        policies=policies,
    )


def policy(config_loader: ConfigLoader, name: str, **changes: object) -> Policy:
    return replace(
        config_loader.to_policy(config_loader.load_policy(name)),
        **changes,
    )


def test_policy_activation_boundaries(config_loader: ConfigLoader) -> None:
    intervention = policy(config_loader, "local_alert_policy", start_tick=3, end_tick=5)

    assert not intervention.is_active(2)
    assert intervention.is_active(3)
    assert intervention.is_active(5)
    assert not intervention.is_active(6)


def test_no_policy_effect_before_start(config_loader: ConfigLoader) -> None:
    intervention = policy(config_loader, "global_alert_policy", start_tick=4)
    engine = build_engine(config_loader, [intervention])

    engine.run(3)

    assert engine.snapshot().active_policies == []
    assert engine.snapshot().metrics.mean_alert_exposure == 0
    assert engine.snapshot().metrics.contact_reduction_estimate == 0


def test_global_alert_reaches_all_agents_and_raises_exposure(config_loader: ConfigLoader) -> None:
    intervention = policy(config_loader, "global_alert_policy", start_tick=1)
    engine = build_engine(config_loader, [intervention])

    snapshot = engine.step()

    assert snapshot.metrics.agents_under_global_alert == len(engine.state.agents)
    assert snapshot.metrics.mean_alert_exposure > 0
    assert all(agent.global_alert_exposure > 0 for agent in engine.state.agents)


def test_local_alert_mainly_affects_target_zone(config_loader: ConfigLoader) -> None:
    intervention = policy(config_loader, "local_alert_policy", start_tick=1)
    engine = build_engine(config_loader, [intervention])
    target = [agent for agent in engine.state.agents if agent.zone_id == "market"]
    outside = [agent for agent in engine.state.agents if agent.zone_id != "market"]

    update = InformationEngine().step(engine.state.agents, (intervention,), tick=1)

    assert target
    assert all(agent.local_alert_exposure > 0 for agent in target)
    assert all(agent.local_alert_exposure == 0 for agent in outside)
    assert update.local_reach == len(target)


def test_zone_closure_reduces_market_contacts(config_loader: ConfigLoader) -> None:
    baseline = build_engine(config_loader, [], seed=91, simulation_id="baseline")
    closure = policy(config_loader, "market_zone_closure_policy", start_tick=1, end_tick=24)
    treated = build_engine(config_loader, [closure], seed=91, simulation_id="closure")

    baseline_snapshot = baseline.run(12)
    treated_snapshot = treated.run(12)
    baseline_market = next(item for item in baseline_snapshot.contact_summary if item.zone_id == "market")
    treated_market = next(item for item in treated_snapshot.contact_summary if item.zone_id == "market")

    assert treated_market.contact_count < baseline_market.contact_count
    assert treated_snapshot.metrics.contact_reduction_estimate > 0


def test_isolation_encouragement_isolates_compliant_symptomatic_agent(
    config_loader: ConfigLoader,
) -> None:
    intervention = policy(
        config_loader,
        "isolation_encouragement_policy",
        start_tick=1,
        compliance_requirement=0.0,
    )
    engine = build_engine(config_loader, [intervention], seed=12)
    agent = engine.state.agents[0]
    agent.state = EpidemiologicalState.INFECTED_SYMPTOMATIC
    agent.infected_at_tick = 0
    agent.infectiousness = 1.0

    snapshot = engine.step()

    assert agent.state == EpidemiologicalState.ISOLATED
    assert snapshot.metrics.isolated_count >= 1


def test_policy_simulation_remains_deterministic(config_loader: ConfigLoader) -> None:
    policies = [
        policy(config_loader, "local_alert_policy", start_tick=1),
        policy(config_loader, "isolation_encouragement_policy", start_tick=1),
    ]
    first = build_engine(config_loader, policies, seed=404, simulation_id="same")
    second = build_engine(config_loader, policies, seed=404, simulation_id="same")

    assert asdict(first.run(36)) == asdict(second.run(36))
