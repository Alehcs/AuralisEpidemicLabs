"""Information exposure model for official alerts and rumors.

This engine only updates bounded *exposure* signals on each agent. Turning those
signals into perceived risk, trust, fatigue and compliance is the job of the
``CognitionEngine`` so that information and cognition stay cleanly separated.

Propagation is deliberately coarse: an event reaches an agent when they are in
its target zone (or it is global), weighted by a deterministic ``intensity *
reach`` salience. There is no per-agent randomness and no pair-level spreading.
"""

from dataclasses import dataclass

from app.domain.agent import Agent
from app.domain.information import InformationEvent, InformationType
from app.domain.policy import Policy, PolicyType

# Exposure signals fade each tick so stale messages stop dominating perception.
_OFFICIAL_DECAY = 0.96
_RUMOR_DECAY = 0.92
_EXPOSED_THRESHOLD = 0.01


@dataclass(frozen=True, slots=True)
class InformationUpdate:
    """Counts of agents currently reached by each information channel."""

    local_reach: int = 0
    global_reach: int = 0
    official_reach: int = 0
    rumor_reach: int = 0
    false_safety_reach: int = 0
    false_danger_reach: int = 0
    anti_authority_reach: int = 0
    active_event_ids: tuple[str, ...] = ()


class InformationEngine:
    """Update bounded official-alert and rumor exposure for every agent."""

    def step(
        self,
        agents: list[Agent],
        policies: tuple[Policy, ...],
        tick: int,
        events: tuple[InformationEvent, ...] = (),
    ) -> InformationUpdate:
        active_events = tuple(event for event in events if event.is_active(tick))
        local_reached: set[str] = set()
        global_reached: set[str] = set()
        official_reached: set[str] = set()
        rumor_reached: set[str] = set()
        false_safety_reached: set[str] = set()
        false_danger_reached: set[str] = set()
        anti_authority_reached: set[str] = set()

        for agent in agents:
            self._decay(agent)
            self._apply_policy_alerts(
                agent, policies, tick, local_reached, global_reached
            )
            for event in active_events:
                if not (event.is_global or agent.zone_id == event.target_zone_id):
                    continue
                self._apply_event(
                    agent,
                    event,
                    official_reached,
                    rumor_reached,
                    false_safety_reached,
                    false_danger_reached,
                    anti_authority_reached,
                )

        official_reached |= local_reached | global_reached
        return InformationUpdate(
            local_reach=len(local_reached),
            global_reach=len(global_reached),
            official_reach=len(official_reached),
            rumor_reach=len(rumor_reached),
            false_safety_reach=len(false_safety_reached),
            false_danger_reach=len(false_danger_reached),
            anti_authority_reach=len(anti_authority_reached),
            active_event_ids=tuple(event.id for event in active_events),
        )

    @staticmethod
    def _decay(agent: Agent) -> None:
        agent.alert_exposure = round(agent.alert_exposure * _OFFICIAL_DECAY, 6)
        agent.official_alert_exposure = round(
            agent.official_alert_exposure * _OFFICIAL_DECAY, 6
        )
        agent.local_alert_exposure = round(agent.local_alert_exposure * _OFFICIAL_DECAY, 6)
        agent.global_alert_exposure = round(
            agent.global_alert_exposure * _OFFICIAL_DECAY, 6
        )
        agent.rumor_exposure = round(agent.rumor_exposure * _RUMOR_DECAY, 6)
        agent.safety_rumor_exposure = round(agent.safety_rumor_exposure * _RUMOR_DECAY, 6)
        agent.danger_rumor_exposure = round(agent.danger_rumor_exposure * _RUMOR_DECAY, 6)
        agent.anti_authority_exposure = round(
            agent.anti_authority_exposure * _RUMOR_DECAY, 6
        )

    def _apply_policy_alerts(
        self,
        agent: Agent,
        policies: tuple[Policy, ...],
        tick: int,
        local_reached: set[str],
        global_reached: set[str],
    ) -> None:
        for policy in policies:
            if policy.policy_type not in {PolicyType.LOCAL_ALERT, PolicyType.GLOBAL_ALERT}:
                continue
            is_global = (
                policy.policy_type == PolicyType.GLOBAL_ALERT or policy.scope == "global"
            )
            if not (is_global or agent.zone_id == policy.target_zone_id):
                continue
            exposure_gain = policy.intensity * (0.025 + 0.015 * agent.compliance_tendency)
            agent.alert_exposure = self._bounded(agent.alert_exposure + exposure_gain)
            agent.official_alert_exposure = agent.alert_exposure
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

    def _apply_event(
        self,
        agent: Agent,
        event: InformationEvent,
        official_reached: set[str],
        rumor_reached: set[str],
        false_safety_reached: set[str],
        false_danger_reached: set[str],
        anti_authority_reached: set[str],
    ) -> None:
        salience = event.intensity * event.reach
        if event.is_official:
            gain = salience * (0.03 + 0.02 * agent.trust_authority) * (0.5 + event.accuracy)
            agent.alert_exposure = self._bounded(agent.alert_exposure + gain)
            agent.official_alert_exposure = self._bounded(
                agent.official_alert_exposure + gain
            )
            if event.is_global:
                agent.global_alert_exposure = self._bounded(
                    agent.global_alert_exposure + gain
                )
            else:
                agent.local_alert_exposure = self._bounded(
                    agent.local_alert_exposure + gain
                )
            official_reached.add(agent.id)
            return

        belief = (
            agent.rumor_belief
            * (1.0 - agent.skepticism)
            * (0.5 + 0.5 * agent.trust_peers)
        )
        weight = self._bounded(salience * belief)
        agent.rumor_exposure = self._bounded(agent.rumor_exposure + weight)
        rumor_reached.add(agent.id)
        if event.event_type == InformationType.FALSE_SAFETY_RUMOR:
            agent.safety_rumor_exposure = self._bounded(
                agent.safety_rumor_exposure + weight
            )
            false_safety_reached.add(agent.id)
        elif event.event_type == InformationType.FALSE_DANGER_RUMOR:
            agent.danger_rumor_exposure = self._bounded(
                agent.danger_rumor_exposure + weight
            )
            false_danger_reached.add(agent.id)
        elif event.event_type == InformationType.PANIC_RUMOR:
            agent.danger_rumor_exposure = self._bounded(
                agent.danger_rumor_exposure + weight * 0.7
            )
            agent.fear = self._bounded(agent.fear + weight * 0.1)
            false_danger_reached.add(agent.id)
        elif event.event_type == InformationType.ANTI_AUTHORITY_RUMOR:
            agent.anti_authority_exposure = self._bounded(
                agent.anti_authority_exposure + weight
            )
            anti_authority_reached.add(agent.id)

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
