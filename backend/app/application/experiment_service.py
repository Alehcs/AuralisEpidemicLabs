"""Batch experiment use cases."""

from app.schemas.configs import ExperimentConfig
from app.schemas.responses import MessageResponse


class ExperimentService:
    """Define the future headless experiment execution boundary."""

    def run(self, experiment: ExperimentConfig) -> MessageResponse:
        """Acknowledge a valid experiment without executing an ABM run yet."""

        return MessageResponse(
            status="placeholder",
            message="Experiment accepted; batch execution arrives in a later phase.",
            data={"experiment_id": experiment.id, "repetitions": experiment.repetitions},
        )
