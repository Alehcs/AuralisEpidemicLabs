"""Deterministic simulation engine tests."""

from dataclasses import asdict


def population_signature(engine) -> list[tuple[str, str, str, str]]:
    return [
        (agent.id, agent.profile, agent.zone_id, agent.state.value)
        for agent in engine.state.agents
    ]


def test_same_seed_produces_same_initial_population(engine_factory) -> None:
    first = engine_factory(seed=730, simulation_id="same")
    second = engine_factory(seed=730, simulation_id="same")

    assert population_signature(first) == population_signature(second)


def test_engine_steps_once_and_preserves_population(engine_factory) -> None:
    engine = engine_factory()
    population_size = len(engine.state.agents)

    snapshot = engine.step()

    assert snapshot.tick == 1
    assert engine.current_step == 1
    assert sum(snapshot.agents_summary.values()) == population_size
    assert len(engine.state.metrics_history) == 2


def test_same_seed_produces_same_first_snapshot(engine_factory) -> None:
    first = engine_factory(seed=99, simulation_id="deterministic")
    second = engine_factory(seed=99, simulation_id="deterministic")

    assert asdict(first.step()) == asdict(second.step())


def test_initial_infections_progress_to_recovered(engine_factory) -> None:
    engine = engine_factory(seed=17)

    snapshot = engine.run(228)

    assert snapshot.metrics.recovered_count >= 12
    assert snapshot.metrics.cumulative_infections >= 12
