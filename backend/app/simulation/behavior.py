"""Deterministic behavior engine translating cognition into protective action.

This engine runs once per tick, after cognition and before mobility/contacts/
transmission. It turns each agent's cognitive state (perceived risk, compliance,
trust, fatigue, fear, curiosity and rumor exposure) into bounded, interpretable
behavior indices that the epidemic core consumes:

* ``protection_behavior`` / ``masking_or_precaution_level`` — abstract precaution
  intensity that lowers infection probability (incoming and outgoing).
* ``distancing_behavior`` — voluntary contact reduction.
* ``risk_compensation`` — extra risky mixing from feeling falsely safe / fatigued.
* ``risky_optional_movement_bias`` — pull toward optional/social trips.

There is no randomness, so identical seeds and configs reproduce identical
behavior. All outputs are clamped to [0, 1].
"""

from app.domain.agent import Agent
from app.domain.behavior_params import BehaviorParameters
from app.simulation.policies import PolicyModifiers


class BehaviorEngine:
    """Compute bounded protective/risky behavior from cognitive state."""

    def step(
        self,
        agents: list[Agent],
        modifiers: PolicyModifiers,
        tick: int,
        params: BehaviorParameters | None = None,
    ) -> None:
        params = params or BehaviorParameters()
        for agent in agents:
            believed_safety = agent.safety_rumor_exposure * agent.rumor_belief
            anti_authority = agent.anti_authority_exposure * agent.rumor_belief

            # Protection rises with perceived risk, compliance, trusted official
            # alerts and peer warnings; fatigue, believed safety and distrust
            # erode it.
            protection = (
                0.45 * agent.perceived_risk
                + 0.30 * agent.adaptive_compliance
                + 0.20 * agent.trust_authority * agent.official_alert_exposure
            )
            protection *= 1.0 - params.fatigue_protection_penalty * agent.fatigue
            protection -= 0.30 * believed_safety
            protection -= params.anti_authority_compliance_penalty * anti_authority
            protection += params.peer_warning_protection_boost * agent.peer_warning_exposure
            agent.protection_behavior = self._bounded(protection)
            agent.masking_or_precaution_level = agent.protection_behavior

            # Distancing tracks fear and perceived risk, dampened by fatigue and
            # false-safety beliefs.
            distancing = (
                0.50 * agent.perceived_risk
                + 0.30 * agent.adaptive_compliance
                + 0.20 * agent.fear
            )
            distancing *= 1.0 - 0.30 * agent.fatigue
            distancing -= 0.25 * believed_safety
            agent.distancing_behavior = self._bounded(distancing)

            # Risk compensation: complacency from believed safety, fatigue and a
            # low personal sense of risk.
            agent.risk_compensation = self._bounded(
                params.false_safety_amplification_strength * believed_safety
                + 0.30 * agent.fatigue
                + 0.25 * max(0.0, 0.5 - agent.perceived_risk)
            )

            # Optional/social movement pull: curiosity and fatigue push agents
            # out, believed safety adds to it, perceived risk holds them back.
            agent.risky_optional_movement_bias = self._bounded(
                0.40 * agent.curiosity
                + 0.30 * agent.fatigue
                + 0.30 * believed_safety
                - 0.40 * agent.perceived_risk
            )

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
