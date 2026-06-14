"""Metrics captured from a simulation state."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Immutable aggregate measurements for one simulation step."""

    step: int
    susceptible: int = 0
    exposed: int = 0
    infectious: int = 0
    recovered: int = 0
    indicators: dict[str, float] = field(default_factory=dict)
