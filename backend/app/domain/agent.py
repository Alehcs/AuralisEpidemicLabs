"""Agent entities and epidemiological state."""

from dataclasses import dataclass, field
from enum import StrEnum


class EpidemiologicalState(StrEnum):
    """Coarse health states to be refined by the transmission model."""

    SUSCEPTIBLE = "susceptible"
    EXPOSED = "exposed"
    INFECTIOUS = "infectious"
    RECOVERED = "recovered"


@dataclass(slots=True)
class Agent:
    """A future autonomous actor combining health, cognition, and location.

    The initial entity intentionally stores only coarse state. Later phases
    will add memory, trust networks, fatigue, routines, and policy response.
    """

    id: str
    profile: str
    zone_id: str
    epidemiological_state: EpidemiologicalState = EpidemiologicalState.SUSCEPTIBLE
    perceived_risk: float = 0.0
    trust: float = 0.5
    fatigue: float = 0.0
    memory: list[str] = field(default_factory=list)
