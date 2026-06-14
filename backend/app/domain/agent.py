"""Agent entities and epidemiological state."""

from dataclasses import dataclass, field
from enum import StrEnum


class EpidemiologicalState(StrEnum):
    """Minimal agent health states used by the Phase 1 disease cycle."""

    SUSCEPTIBLE = "susceptible"
    EXPOSED = "exposed"
    INFECTED_ASYMPTOMATIC = "infected_asymptomatic"
    INFECTED_SYMPTOMATIC = "infected_symptomatic"
    RECOVERED = "recovered"
    ISOLATED = "isolated"


class RoutineType(StrEnum):
    """Minimal schedule archetypes used by deterministic mobility."""

    WORKER = "worker"
    STUDENT = "student"
    REMOTE = "remote"
    ELDERLY = "elderly"
    TRADER = "trader"
    HEALTHCARE = "healthcare"
    UNEMPLOYED = "unemployed"


@dataclass(slots=True)
class Agent:
    """A future autonomous actor combining health, cognition, and location.

    The initial entity intentionally stores only coarse state. Later phases
    will add memory, trust networks, fatigue, routines, and policy response.
    """

    id: str
    profile: str
    zone_id: str
    home_zone_id: str
    work_zone_id: str | None
    school_zone_id: str | None
    routine_type: RoutineType
    movement_tendency: float
    current_intended_destination: str | None = None
    last_moved_tick: int | None = None
    state: EpidemiologicalState = EpidemiologicalState.SUSCEPTIBLE
    exposed_at_tick: int | None = None
    infected_at_tick: int | None = None
    recovered_at_tick: int | None = None
    infectiousness: float = 0.0
    perceived_risk: float = 0.0
    trust: float = 0.5
    fatigue: float = 0.0
    memory: list[str] = field(default_factory=list)

    @property
    def is_infectious(self) -> bool:
        """Return whether the agent can contribute to transmission."""

        return self.state in {
            EpidemiologicalState.INFECTED_ASYMPTOMATIC,
            EpidemiologicalState.INFECTED_SYMPTOMATIC,
        }
