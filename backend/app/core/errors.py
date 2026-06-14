"""Application-level exceptions independent from HTTP transport details."""


class AuralisError(Exception):
    """Base exception for expected Auralis application failures."""


class ConfigNotFoundError(AuralisError):
    """Raised when a named declarative configuration cannot be found."""


class SimulationNotFoundError(AuralisError):
    """Raised when an in-memory simulation identifier is unknown."""
