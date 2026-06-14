"""Simulation orchestration smoke tests."""

from app.simulation.engine import SimulationEngine


def test_engine_instantiates_and_advances() -> None:
    engine = SimulationEngine(simulation_id="test-run")

    snapshot = engine.step()

    assert engine.current_step == 1
    assert snapshot["simulation_id"] == "test-run"
    assert snapshot["step"] == 1
