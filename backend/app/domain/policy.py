"""Policy intervention domain models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Policy:
    """A scheduled intervention exposed through no-op Phase 2 hooks."""

    id: str
    name: str
    scope: str
    policy_type: str
    intensity: float
    start_tick: int
    end_tick: int | None = None
    target_zone_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def is_active(self, tick: int) -> bool:
        """Return whether the policy schedule covers a tick."""

        return tick >= self.start_tick and (self.end_tick is None or tick <= self.end_tick)
