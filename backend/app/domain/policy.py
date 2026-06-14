"""Policy intervention domain models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Policy:
    """A policy that can alter information, mobility, or contact behavior."""

    id: str
    name: str
    scope: str
    parameters: dict[str, Any] = field(default_factory=dict)
