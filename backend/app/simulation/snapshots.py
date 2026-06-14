"""Serializable simulation state snapshots."""

from typing import Any


class SnapshotBuilder:
    """Build stable snapshots for APIs, files, and future replay tooling."""

    def create_snapshot(
        self,
        simulation_id: str,
        step: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create the Phase 0 snapshot representation."""

        return {
            "simulation_id": simulation_id,
            "step": step,
            "metadata": metadata or {},
            "metrics": {},
        }
