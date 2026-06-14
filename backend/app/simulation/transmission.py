"""Disease exposure and progression engine boundary."""

from app.domain.agent import Agent
from app.domain.disease import DiseaseProfile
from app.simulation.contacts import ContactPair


class TransmissionEngine:
    """Future engine for exposure, infection, recovery, and severity changes."""

    def step(
        self,
        agents: list[Agent],
        contacts: list[ContactPair],
        disease: DiseaseProfile,
    ) -> list[Agent]:
        """Return agents unchanged until transmission rules are implemented."""

        del contacts, disease
        return agents
