"""Aggregate metric computation boundary."""

from collections import Counter

from app.domain.agent import Agent
from app.domain.metrics import MetricsSnapshot


class MetricsEngine:
    """Compute epidemiological and future socio-cognitive aggregates."""

    def create_snapshot(self, step: int, agents: list[Agent]) -> MetricsSnapshot:
        """Count agents by their current epidemiological state."""

        counts = Counter(agent.epidemiological_state.value for agent in agents)
        return MetricsSnapshot(
            step=step,
            susceptible=counts["susceptible"],
            exposed=counts["exposed"],
            infectious=counts["infectious"],
            recovered=counts["recovered"],
        )
