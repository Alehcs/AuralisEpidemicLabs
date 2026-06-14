"""Deterministic orchestration for one agent-based simulation run."""

import random
from dataclasses import dataclass, field

from app.domain.simulation import SimulationSnapshot, SimulationState
from app.domain.world import World
from app.domain.disease import DiseaseProfile
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig
from app.simulation.metrics import MetricsEngine
from app.simulation.mobility import MobilityEngine
from app.simulation.population import PopulationGenerator
from app.simulation.snapshots import SnapshotBuilder
from app.simulation.transmission import TransmissionEngine


@dataclass(slots=True)
class SimulationEngine:
    """Own mutable state and execute ordered movement and disease phases."""

    state: SimulationState
    rng: random.Random
    mobility_engine: MobilityEngine = field(default_factory=MobilityEngine)
    transmission_engine: TransmissionEngine = field(default_factory=TransmissionEngine)
    metrics_engine: MetricsEngine = field(default_factory=MetricsEngine)
    snapshot_builder: SnapshotBuilder = field(default_factory=SnapshotBuilder)

    @classmethod
    def create(
        cls,
        simulation_id: str,
        world: World,
        disease: DiseaseProfile,
        population_config: AgentPopulationConfig,
        outbreak: InitialOutbreakConfig,
        seed: int,
    ) -> "SimulationEngine":
        """Create a reproducible simulation aggregate from domain inputs."""

        agents = PopulationGenerator().generate(
            config=population_config,
            world=world,
            disease=disease,
            outbreak=outbreak,
            seed=seed,
        )
        cumulative = outbreak.exposed_agents + outbreak.infected_agents
        state = SimulationState(
            simulation_id=simulation_id,
            seed=seed,
            tick=0,
            world=world,
            disease=disease,
            agents=agents,
            cumulative_infections=cumulative,
        )
        engine = cls(state=state, rng=random.Random(seed))
        state.metrics_history.append(
            engine.metrics_engine.create_snapshot(
                tick=0,
                agents=agents,
                new_infections=0,
                cumulative_infections=cumulative,
            )
        )
        return engine

    @property
    def simulation_id(self) -> str:
        return self.state.simulation_id

    @property
    def current_step(self) -> int:
        """Backward-compatible alias for the current tick."""

        return self.state.tick

    def step(self) -> SimulationSnapshot:
        """Advance movement, progression, transmission, and metrics one tick."""

        self.state.tick += 1
        self.mobility_engine.step(self.state.agents, self.state.world, self.rng)
        new_infections = self.transmission_engine.step(
            agents=self.state.agents,
            world=self.state.world,
            disease=self.state.disease,
            tick=self.state.tick,
            rng=self.rng,
        )
        self.state.new_infections = new_infections
        self.state.cumulative_infections += new_infections
        self.state.metrics_history.append(
            self.metrics_engine.create_snapshot(
                tick=self.state.tick,
                agents=self.state.agents,
                new_infections=new_infections,
                cumulative_infections=self.state.cumulative_infections,
            )
        )
        return self.snapshot()

    def run(self, ticks: int) -> SimulationSnapshot:
        """Advance a positive number of ticks for interactive or batch use."""

        if ticks <= 0:
            raise ValueError("ticks must be greater than zero")
        for _ in range(ticks):
            self.step()
        return self.snapshot()

    def snapshot(self) -> SimulationSnapshot:
        """Return the current compact visualization projection."""

        return self.snapshot_builder.create_snapshot(self.state)

    def create_snapshot(self) -> dict[str, object]:
        """Backward-compatible JSON projection used by existing callers."""

        return self.snapshot_builder.as_dict(self.snapshot())
