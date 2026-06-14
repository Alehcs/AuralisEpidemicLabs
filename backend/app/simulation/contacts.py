"""Contact generation engine boundary."""

from app.domain.agent import Agent

ContactPair = tuple[str, str]


class ContactEngine:
    """Future engine for generating proximity and social contact events."""

    def step(self, agents: list[Agent]) -> list[ContactPair]:
        """Return no contacts until contact-network rules are implemented."""

        del agents
        return []
