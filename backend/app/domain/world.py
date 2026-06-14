"""Spatial entities for the simulated district."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Zone:
    """A functional district area where agents can reside or interact."""

    id: str
    name: str
    kind: str
    capacity: int


@dataclass(frozen=True, slots=True)
class Route:
    """A directed movement connection between two district zones."""

    origin_zone_id: str
    destination_zone_id: str
    travel_cost: float = 1.0


@dataclass(slots=True)
class World:
    """Container for zones, routes, and future environment-level state."""

    zones: dict[str, Zone] = field(default_factory=dict)
    routes: list[Route] = field(default_factory=list)
