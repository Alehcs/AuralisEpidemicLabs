"""Socio-cognitive state update boundary."""

from app.domain.agent import Agent


class CognitionEngine:
    """Future engine for risk perception, trust, fatigue, and memory updates."""

    def step(self, agents: list[Agent]) -> list[Agent]:
        """Return agents unchanged until cognitive rules are implemented."""

        return agents
