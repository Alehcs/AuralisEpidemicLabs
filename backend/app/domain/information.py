"""Information and rumor domain events.

Phase 4 introduces a minimal, interpretable information layer. Official alerts
and rumors are modeled as the same shape of timed event so they can compete for
the same bounded attention budget on each agent. Propagation is intentionally
coarse (zone/global exposure) rather than pair-level network spreading.
"""

from dataclasses import dataclass
from enum import StrEnum


class InformationType(StrEnum):
    """Kinds of messages agents may perceive, believe, or distrust."""

    OFFICIAL_ALERT = "official_alert"
    LOCAL_WARNING = "local_warning"
    FALSE_SAFETY_RUMOR = "false_safety_rumor"
    FALSE_DANGER_RUMOR = "false_danger_rumor"
    ANTI_AUTHORITY_RUMOR = "anti_authority_rumor"
    PANIC_RUMOR = "panic_rumor"


_OFFICIAL_TYPES = frozenset(
    {InformationType.OFFICIAL_ALERT, InformationType.LOCAL_WARNING}
)


@dataclass(frozen=True, slots=True)
class InformationEvent:
    """A timed message reaching a zone (or the whole district when global).

    ``reach`` and ``intensity`` are deterministic scalars in [0, 1] applied as a
    coarse attention weight; no per-agent randomness is used so the same seed and
    configuration always reproduce identical cognitive trajectories.
    """

    id: str
    event_type: InformationType
    source: str
    start_tick: int
    end_tick: int | None = None
    target_zone_id: str | None = None
    intensity: float = 0.5
    reach: float = 0.5
    accuracy: float = 0.5
    decay_rate: float = 0.05

    def is_active(self, tick: int) -> bool:
        """Return whether the event schedule covers a tick."""

        return tick >= self.start_tick and (self.end_tick is None or tick <= self.end_tick)

    @property
    def is_official(self) -> bool:
        """Return whether the event originates from an authority channel."""

        return self.event_type in _OFFICIAL_TYPES

    @property
    def is_rumor(self) -> bool:
        """Return whether the event is unofficial information."""

        return not self.is_official

    @property
    def is_global(self) -> bool:
        """Return whether the event reaches every zone."""

        return self.target_zone_id is None
