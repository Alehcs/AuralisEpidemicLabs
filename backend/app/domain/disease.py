"""Disease domain models independent from configuration transport schemas."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiseaseProfile:
    """Parameters consumed by future exposure and progression algorithms."""

    id: str
    name: str
    beta_base: float
    incubation_days: float
    infectious_days: float
    asymptomatic_probability: float
    tick_minutes: int

    @property
    def ticks_per_day(self) -> float:
        """Number of simulation ticks in one modeled day."""

        return 1440 / self.tick_minutes

    @property
    def incubation_ticks(self) -> int:
        """Incubation duration rounded to at least one tick."""

        return max(1, round(self.incubation_days * self.ticks_per_day))

    @property
    def infectious_ticks(self) -> int:
        """Infectious duration rounded to at least one tick."""

        return max(1, round(self.infectious_days * self.ticks_per_day))
