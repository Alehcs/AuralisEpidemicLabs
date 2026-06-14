"""Deterministic socio-cognitive state updates.

The engine runs once per tick, after information has been processed and before
mobility, and rewrites each agent's perceived risk, trust, fatigue, memory and
adaptive compliance from simple, documented formulas. There is no randomness, so
identical seeds and configs reproduce identical cognitive trajectories.

All agent cognitive attributes are kept bounded to [0, 1]. ``perceived_risk`` is
recomputed from scratch every tick so it always reflects the current blend of
real risk, official information, rumors, memory, trust and fatigue.
"""

from app.domain.agent import Agent, EpidemiologicalState
from app.domain.policy import PolicyType
from app.simulation.policies import PolicyModifiers

# Below this local active-infection ratio an official alert is treated as "not
# matching visible risk", which slowly erodes trust in authority.
ALERT_REAL_THRESHOLD = 0.015


class CognitionEngine:
    """Update risk perception, trust, fatigue, memory and compliance."""

    def step(
        self,
        agents: list[Agent],
        real_risk_by_zone: dict[str, float],
        modifiers: PolicyModifiers,
        tick: int,
    ) -> None:
        global_alert_active = any(
            policy.policy_type == PolicyType.GLOBAL_ALERT
            for policy in modifiers.active_policies
        )
        closed_zones = modifiers.closed_zones
        for agent in agents:
            real = real_risk_by_zone.get(agent.zone_id, 0.0)
            agent.real_risk = round(real, 6)
            self._update_memory(agent, real)
            self._update_trust(agent, real)
            self._update_fatigue(agent, global_alert_active, closed_zones)
            self._update_fear(agent, real)
            agent.perceived_risk = self._perceived_risk(agent, real)
            agent.memory_risk = self._bounded(
                agent.memory_risk * 0.92 + 0.08 * max(real, agent.perceived_risk)
            )
            agent.adaptive_compliance = self._compliance(agent)

    @staticmethod
    def _update_memory(agent: Agent, real: float) -> None:
        # Slowly decaying memory of recent local infections; personal symptomatic
        # or isolation experience leaves a stronger trace.
        agent.memory_recent_infections_nearby = CognitionEngine._bounded(
            agent.memory_recent_infections_nearby * 0.94 + real * 0.06
        )
        if agent.state in {
            EpidemiologicalState.INFECTED_SYMPTOMATIC,
            EpidemiologicalState.ISOLATED,
        }:
            agent.memory_recent_infections_nearby = CognitionEngine._bounded(
                agent.memory_recent_infections_nearby + 0.02
            )

    @staticmethod
    def _update_trust(agent: Agent, real: float) -> None:
        official = agent.official_alert_exposure
        if official > 0.05:
            if real >= ALERT_REAL_THRESHOLD:
                # Visible local risk with an active alert builds trust.
                agent.trust_authority = CognitionEngine._bounded(
                    agent.trust_authority + 0.004 * official
                )
                agent.memory_alert_accuracy = CognitionEngine._bounded(
                    agent.memory_alert_accuracy + 0.01
                )
            else:
                # Repeated alerts without visible risk erode trust.
                agent.trust_authority = CognitionEngine._bounded(
                    agent.trust_authority - 0.006 * official
                )
                agent.memory_alert_accuracy = CognitionEngine._bounded(
                    agent.memory_alert_accuracy - 0.012
                )
        if agent.anti_authority_exposure > 0:
            agent.trust_authority = CognitionEngine._bounded(
                agent.trust_authority
                - 0.05 * agent.anti_authority_exposure * agent.rumor_belief
            )

    @staticmethod
    def _update_fatigue(
        agent: Agent,
        global_alert_active: bool,
        closed_zones: frozenset[str],
    ) -> None:
        restriction = 0.0
        if global_alert_active:
            restriction += 0.6
        if agent.zone_id in closed_zones:
            restriction += 0.8
        if agent.state == EpidemiologicalState.ISOLATED:
            restriction += 1.0
        # Repeated official alerts also wear agents down.
        restriction += 0.4 * agent.official_alert_exposure
        if restriction > 0.0:
            agent.fatigue = CognitionEngine._bounded(agent.fatigue + 0.01 * restriction)
        else:
            # Slow recovery during low-risk, no-policy periods.
            agent.fatigue = CognitionEngine._bounded(agent.fatigue - 0.006)

    @staticmethod
    def _update_fear(agent: Agent, real: float) -> None:
        fear_drive = 0.4 * agent.danger_rumor_exposure * agent.rumor_belief + 0.5 * real
        agent.fear = CognitionEngine._bounded(agent.fear * 0.9 + 0.1 * fear_drive)

    @staticmethod
    def _perceived_risk(agent: Agent, real: float) -> float:
        believed_safety = (
            agent.safety_rumor_exposure * agent.rumor_belief * (1.0 - agent.skepticism)
        )
        believed_danger = agent.danger_rumor_exposure * agent.rumor_belief
        perceived = (
            0.40 * real
            + 0.25 * agent.official_alert_exposure * agent.trust_authority
            + 0.15 * agent.memory_recent_infections_nearby
            + 0.12 * believed_danger
            + 0.10 * agent.fear
            + 0.10 * agent.peer_warning_exposure * agent.trust_peers
            - 0.30 * believed_safety
        )
        # Fatigue dampens responsiveness to all signals (perception numbing).
        perceived *= 1.0 - 0.25 * agent.fatigue
        return CognitionEngine._bounded(perceived)

    @staticmethod
    def _compliance(agent: Agent) -> float:
        compliance = (
            0.40 * agent.compliance_tendency
            + 0.30 * agent.trust_authority
            + 0.30 * agent.perceived_risk
        )
        compliance *= 1.0 - 0.40 * agent.fatigue
        compliance -= 0.15 * agent.skepticism
        return CognitionEngine._bounded(compliance)

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
