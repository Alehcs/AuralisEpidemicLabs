"""Disease domain models independent from configuration transport schemas."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiseaseProfile:
    """Parameters consumed by future exposure and progression algorithms."""

    id: str
    name: str
    transmission_probability: float
    incubation_days: float
    infectious_days: float
