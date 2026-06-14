"""Shared Phase 1 simulation test fixtures."""

from pathlib import Path

import pytest

from app.infrastructure.config_loader import ConfigLoader
from app.simulation.engine import SimulationEngine

CONFIGS_DIRECTORY = Path(__file__).resolve().parents[2] / "configs"


@pytest.fixture
def config_loader() -> ConfigLoader:
    return ConfigLoader(CONFIGS_DIRECTORY)


@pytest.fixture
def engine_factory(config_loader: ConfigLoader):
    def create(
        seed: int = 42,
        simulation_id: str = "test-simulation",
        with_policy: bool = True,
        policy_names: list[str] | None = None,
    ) -> SimulationEngine:
        scenario = config_loader.load_scenario("district_v1_market_outbreak")
        disease = config_loader.load_disease("respiratory_like_v1")
        population = config_loader.load_population("default_population_v1")
        names = policy_names if policy_names is not None else (
            ["local_alert_policy"] if with_policy else []
        )
        policies = [
            config_loader.to_policy(config_loader.load_policy(name)) for name in names
        ]
        return SimulationEngine.create(
            simulation_id=simulation_id,
            world=config_loader.to_world(scenario),
            disease=config_loader.to_disease(disease),
            population_config=population,
            outbreak=scenario.initial_outbreak,
            seed=seed,
            policy=policies[0] if len(policies) == 1 else None,
            policies=policies,
            config_summary={"seed": seed},
        )

    return create
