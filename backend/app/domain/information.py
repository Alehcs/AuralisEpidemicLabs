"""Information and rumor domain events."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InformationEvent:
    """A message agents may perceive, trust, remember, or retransmit."""

    id: str
    source: str
    content: str
    credibility: float
    target_zone_id: str | None = None
