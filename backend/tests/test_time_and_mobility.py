"""Time projection and deterministic schedule mobility tests."""

import random

from app.domain.agent import EpidemiologicalState, RoutineType
from app.domain.time import SimulationTime, TimeOfDayLabel
from app.simulation.mobility import MobilityEngine


def assignment_signature(engine) -> list[tuple[str, str, str | None, str | None, str]]:
    return [
        (
            agent.id,
            agent.home_zone_id,
            agent.work_zone_id,
            agent.school_zone_id,
            agent.routine_type.value,
        )
        for agent in engine.state.agents
    ]


def test_time_model_converts_tick_to_calendar_fields() -> None:
    time = SimulationTime.from_tick(37, 30)

    assert time.day == 0
    assert time.hour == 18
    assert time.minute == 30
    assert time.time_of_day_label == TimeOfDayLabel.EVENING_COMMUTE


def test_home_work_assignments_are_seeded(engine_factory) -> None:
    first = engine_factory(seed=501)
    second = engine_factory(seed=501)
    different = engine_factory(seed=502)

    assert assignment_signature(first) == assignment_signature(second)
    assert assignment_signature(first) != assignment_signature(different)
    assert all(agent.home_zone_id in first.state.world.zones for agent in first.state.agents)


def test_worker_moves_toward_work_during_commute(engine_factory) -> None:
    engine = engine_factory(seed=41)
    agent = next(
        item
        for item in engine.state.agents
        if item.routine_type == RoutineType.WORKER
        and item.work_zone_id
        and engine.state.world.next_hop(item.home_zone_id, item.work_zone_id)
    )
    agent.zone_id = agent.home_zone_id

    moved = MobilityEngine().step(
        [agent],
        engine.state.world,
        SimulationTime.from_tick(6, 60),
        random.Random(1),
    )

    assert moved == 1
    assert agent.last_moved_tick == 6
    assert agent.current_intended_destination == agent.work_zone_id


def test_isolated_agent_does_not_move(engine_factory) -> None:
    engine = engine_factory(seed=41)
    agent = next(item for item in engine.state.agents if item.work_zone_id)
    agent.zone_id = agent.home_zone_id
    agent.state = EpidemiologicalState.ISOLATED

    moved = MobilityEngine().step(
        [agent],
        engine.state.world,
        SimulationTime.from_tick(6, 60),
        random.Random(1),
    )

    assert moved == 0
    assert agent.zone_id == agent.home_zone_id
