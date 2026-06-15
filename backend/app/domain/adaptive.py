"""Adaptive intervention domain model.

Adaptive policies are deterministic, rule-based reactions to live simulation
metrics. Each rule watches one metric; when the comparison holds and the rule is
not in cooldown, it activates an intervention for a bounded number of ticks. This
is intentionally simple (no optimization or learning) and fully reproducible.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class AdaptiveAction(StrEnum):
    """Interventions an adaptive rule can activate."""

    COUNTER_MESSAGING = "counter_messaging"
    PEER_WARNING_CAMPAIGN = "peer_warning_campaign"
    TRUST_REPAIR_MESSAGE = "trust_repair_message"
    TARGETED_LOCAL_ALERT = "targeted_local_alert"
    ADAPTIVE_ISOLATION_ENCOURAGEMENT = "adaptive_isolation_encouragement"


_VALID_OPERATORS = frozenset({">", "<", ">=", "<=", "=="})


@dataclass(frozen=True, slots=True)
class AdaptiveRule:
    """One metric-triggered reaction with duration, intensity and cooldown."""

    id: str
    metric: str
    operator: str
    threshold: float
    action: AdaptiveAction
    target: str = "global"
    target_zone_id: str | None = None
    duration_ticks: int = 24
    intensity: float = 0.5
    cooldown_ticks: int = 24

    def __post_init__(self) -> None:
        if self.operator not in _VALID_OPERATORS:
            raise ValueError(f"Unsupported adaptive operator: {self.operator}")


@dataclass(frozen=True, slots=True)
class AdaptivePolicy:
    """A named bundle of adaptive rules."""

    id: str
    rules: tuple[AdaptiveRule, ...] = ()


@dataclass(slots=True)
class ActiveIntervention:
    """A currently active adaptive intervention with a mutable end tick."""

    rule_id: str
    action: AdaptiveAction
    target: str
    target_zone_id: str | None
    intensity: float
    start_tick: int
    end_tick: int

    def covers(self, zone_id: str) -> bool:
        """Return whether the intervention applies to a given zone."""

        return self.target == "global" or self.target_zone_id == zone_id
