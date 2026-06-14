"""Spatial entities for the simulated district."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Zone:
    """A functional district area where agents can reside or interact."""

    id: str
    name: str
    kind: str
    capacity: int
    contact_rate: float = 1.0
    movement_weight: float = 1.0


@dataclass(frozen=True, slots=True)
class Route:
    """A directed movement connection between two district zones."""

    origin_zone_id: str
    destination_zone_id: str
    travel_weight: float = 1.0


@dataclass(slots=True)
class World:
    """Container for zones, routes, and future environment-level state."""

    zones: dict[str, Zone] = field(default_factory=dict)
    routes: list[Route] = field(default_factory=list)

    def destinations_from(self, zone_id: str) -> list[Route]:
        """Return configured outgoing routes from one zone."""

        return [route for route in self.routes if route.origin_zone_id == zone_id]

    def next_hop(self, origin_zone_id: str, destination_zone_id: str) -> str | None:
        """Return the deterministic first hop on a shortest directed route."""

        if origin_zone_id == destination_zone_id:
            return destination_zone_id
        queue: list[tuple[str, str]] = []
        visited = {origin_zone_id}
        for route in sorted(
            self.destinations_from(origin_zone_id),
            key=lambda item: (item.destination_zone_id, item.travel_weight),
        ):
            queue.append((route.destination_zone_id, route.destination_zone_id))
            visited.add(route.destination_zone_id)
        while queue:
            zone_id, first_hop = queue.pop(0)
            if zone_id == destination_zone_id:
                return first_hop
            for route in sorted(
                self.destinations_from(zone_id),
                key=lambda item: (item.destination_zone_id, item.travel_weight),
            ):
                if route.destination_zone_id not in visited:
                    visited.add(route.destination_zone_id)
                    queue.append((route.destination_zone_id, first_hop))
        return None
