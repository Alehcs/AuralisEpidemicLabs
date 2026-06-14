"""Policy intervention definitions and activation rules."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PolicyType(StrEnum):
    """Interventions with concrete Phase 3 simulation effects."""

    LOCAL_ALERT = "local_alert"
    GLOBAL_ALERT = "global_alert"
    ZONE_CLOSURE = "zone_closure"
    ISOLATION_ENCOURAGEMENT = "isolation_encouragement"


@dataclass(frozen=True, slots=True)
class Policy:
    """A scheduled intervention with bounded behavioral modifiers."""

    id: str
    name: str
    scope: str
    policy_type: PolicyType
    intensity: float
    start_tick: int
    end_tick: int | None = None
    target_zone_id: str | None = None
    compliance_requirement: float = 0.0
    mobility_impact: float = 0.0
    contact_impact: float = 0.0
    transmission_impact: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)

    def is_active(self, tick: int) -> bool:
        """Return whether the policy schedule covers a tick."""

        return tick >= self.start_tick and (self.end_tick is None or tick <= self.end_tick)
