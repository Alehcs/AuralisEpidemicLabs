"""Minimal official-alert information exposure model."""

from dataclasses import dataclass

from app.domain.agent import Agent
from app.domain.policy import Policy, PolicyType


@dataclass(frozen=True, slots=True)
class InformationUpdate:
    """Counts of agents reached by currently active official alerts."""

    local_reach: int = 0
    global_reach: int = 0


class InformationEngine:
    """Update bounded alert exposure and perceived risk without rumors yet."""

    def step(
        self,
        agents: list[Agent],
        policies: tuple[Policy, ...],
        tick: int,
    ) -> InformationUpdate:
        local_reached: set[str] = set()
        global_reached: set[str] = set()

        for agent in agents:
            agent.perceived_risk = round(max(0.0, agent.perceived_risk * 0.998), 6)
            for policy in policies:
                if policy.policy_type not in {PolicyType.LOCAL_ALERT, PolicyType.GLOBAL_ALERT}:
                    continue
                is_global = policy.policy_type == PolicyType.GLOBAL_ALERT or policy.scope == "global"
                reached = is_global or agent.zone_id == policy.target_zone_id
                if not reached:
                    continue
                exposure_gain = policy.intensity * (0.025 + 0.015 * agent.compliance_tendency)
                risk_gain = exposure_gain * (0.55 + 0.35 * agent.compliance_tendency)
                agent.alert_exposure = self._bounded(agent.alert_exposure + exposure_gain)
                agent.official_alert_exposure = agent.alert_exposure
                agent.perceived_risk = self._bounded(agent.perceived_risk + risk_gain)
                agent.last_alert_tick = tick
                agent.policy_memory[policy.id] = self._bounded(
                    agent.policy_memory.get(policy.id, 0.0) + exposure_gain
                )
                if is_global:
                    agent.global_alert_exposure = self._bounded(
                        agent.global_alert_exposure + exposure_gain
                    )
                    global_reached.add(agent.id)
                else:
                    agent.local_alert_exposure = self._bounded(
                        agent.local_alert_exposure + exposure_gain
                    )
                    local_reached.add(agent.id)

        return InformationUpdate(
            local_reach=len(local_reached),
            global_reach=len(global_reached),
        )

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
