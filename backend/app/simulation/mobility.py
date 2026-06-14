"""Agent movement engine boundary."""

from app.domain.agent import Agent
from app.domain.world import World


class MobilityEngine:
    """Future engine for routines, route choice, and mobility restrictions."""

    def step(self, agents: list[Agent], world: World) -> list[Agent]:
        """Return agents unchanged until mobility rules are implemented."""

        del world
        return agents
