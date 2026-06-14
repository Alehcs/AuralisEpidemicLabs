"""Deterministic simulation phase scheduling."""

from dataclasses import dataclass


@dataclass(slots=True)
class SimulationScheduler:
    """Track ticks and later order the engines executed during each tick."""

    current_step: int = 0

    def step(self) -> int:
        """Advance and return the current simulation tick."""

        self.current_step += 1
        return self.current_step

    def run(self, steps: int) -> int:
        """Advance multiple scheduler ticks."""

        if steps < 0:
            raise ValueError("steps must be non-negative")
        self.current_step += steps
        return self.current_step
