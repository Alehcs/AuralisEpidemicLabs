"""Compact contact observations retained per zone and tick."""

from dataclasses import dataclass


@dataclass(slots=True)
class ContactRecord:
    """Aggregated local contacts without storing all agent pairs."""

    tick: int
    zone_id: str
    contact_count: int
    susceptible_exposed_contacts: int
    infectious_contacts: int
    new_infections: int
    average_zone_density: float
