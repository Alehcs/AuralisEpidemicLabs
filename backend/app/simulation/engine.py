"""Top-level orchestration for a single simulation run."""

from dataclasses import dataclass, field
from typing import Any

from app.simulation.scheduler import SimulationScheduler
from app.simulation.snapshots import SnapshotBuilder


@dataclass(slots=True)
class SimulationEngine:
    """Coordinate simulation phases without depending on delivery adapters.

    Phase 0 advances only the scheduler and returns a coarse snapshot. Future
    phases will compose cognition, mobility, contacts, and transmission here.
    """

    simulation_id: str = "local-simulation"
    scheduler: SimulationScheduler = field(default_factory=SimulationScheduler)
    snapshot_builder: SnapshotBuilder = field(default_factory=SnapshotBuilder)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def current_step(self) -> int:
        """Expose the scheduler step for clients and tests."""

        return self.scheduler.current_step

    def step(self) -> dict[str, Any]:
        """Advance one placeholder tick and return a serializable snapshot."""

        self.scheduler.step()
        return self.create_snapshot()

    def run(self, steps: int = 1) -> dict[str, Any]:
        """Advance a fixed number of ticks for future headless execution."""

        if steps < 0:
            raise ValueError("steps must be non-negative")
        for _ in range(steps):
            self.step()
        return self.create_snapshot()

    def create_snapshot(self) -> dict[str, Any]:
        """Build a transport-neutral summary of the current state."""

        return self.snapshot_builder.create_snapshot(
            simulation_id=self.simulation_id,
            step=self.current_step,
            metadata=self.metadata,
        )
