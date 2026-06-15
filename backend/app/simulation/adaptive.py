"""Deterministic, rule-based adaptive intervention engine.

Each tick the engine evaluates an :class:`AdaptivePolicy`'s rules against a
context of the latest metrics (and current per-zone real risk). When a rule's
comparison holds and it is not in cooldown, it activates an intervention for a
bounded number of ticks; re-firing while active extends (escalates) it, and
interventions expire automatically. Effects are simple, measurable mutations of
agent state. No randomness is used, so behavior is fully reproducible.
"""

from dataclasses import dataclass, field
from operator import eq, ge, gt, le, lt

from app.domain.adaptive import ActiveIntervention, AdaptiveAction, AdaptivePolicy
from app.domain.agent import Agent, EpidemiologicalState

_OPERATORS = {">": gt, "<": lt, ">=": ge, "<=": le, "==": eq}


@dataclass(slots=True)
class AdaptivePolicyEngine:
    """Evaluate adaptive rules and apply their interventions to agents."""

    active: list[ActiveIntervention] = field(default_factory=list)
    last_triggered_tick: dict[str, int] = field(default_factory=dict)
    trigger_count: int = 0
    last_triggered_rule: str | None = None

    def evaluate(
        self,
        policy: AdaptivePolicy | None,
        context: dict[str, float],
        zone_risk: dict[str, float],
        tick: int,
    ) -> list[ActiveIntervention]:
        """Expire ended interventions, then trigger/extend matching rules."""

        self.active = [item for item in self.active if tick <= item.end_tick]
        if policy is None:
            return self.active
        for rule in policy.rules:
            value = self._resolve(rule.metric, rule.target_zone_id, context, zone_risk)
            if value is None:
                continue
            if not _OPERATORS[rule.operator](value, rule.threshold):
                continue
            existing = next(
                (item for item in self.active if item.rule_id == rule.id), None
            )
            if existing is not None:
                existing.end_tick = tick + rule.duration_ticks
                continue
            last = self.last_triggered_tick.get(rule.id)
            if last is not None and tick - last < rule.cooldown_ticks:
                continue
            self.active.append(
                ActiveIntervention(
                    rule_id=rule.id,
                    action=rule.action,
                    target=rule.target,
                    target_zone_id=rule.target_zone_id,
                    intensity=rule.intensity,
                    start_tick=tick,
                    end_tick=tick + rule.duration_ticks,
                )
            )
            self.last_triggered_tick[rule.id] = tick
            self.trigger_count += 1
            self.last_triggered_rule = rule.id
        return self.active

    def apply(self, agents: list[Agent], tick: int) -> None:
        """Apply messaging/alert/trust effects of active interventions."""

        messaging = [
            item
            for item in self.active
            if item.action != AdaptiveAction.ADAPTIVE_ISOLATION_ENCOURAGEMENT
        ]
        if not messaging:
            return
        for agent in agents:
            for intervention in messaging:
                if intervention.covers(agent.zone_id):
                    self._apply_effect(agent, intervention)

    def apply_adaptive_isolation(self, agents: list[Agent], tick: int) -> int:
        """Isolate symptomatic agents under an active adaptive-isolation rule."""

        interventions = [
            item
            for item in self.active
            if item.action == AdaptiveAction.ADAPTIVE_ISOLATION_ENCOURAGEMENT
        ]
        if not interventions:
            return 0
        isolated = 0
        for agent in agents:
            if agent.state != EpidemiologicalState.INFECTED_SYMPTOMATIC:
                continue
            for intervention in interventions:
                if not intervention.covers(agent.zone_id):
                    continue
                threshold = max(0.0, 0.6 - intervention.intensity)
                if agent.isolation_compliance >= threshold:
                    agent.pre_isolation_state = agent.state
                    agent.state = EpidemiologicalState.ISOLATED
                    agent.isolation_started_tick = tick
                    isolated += 1
                    break
        return isolated

    def effect_summary(self) -> dict[str, object]:
        """Return per-action active flags and the active rule ids."""

        actions = {item.action for item in self.active}
        return {
            "active_rule_ids": [item.rule_id for item in self.active],
            "counter_messaging_active": AdaptiveAction.COUNTER_MESSAGING in actions,
            "peer_warning_campaign_active": (
                AdaptiveAction.PEER_WARNING_CAMPAIGN in actions
            ),
            "trust_repair_active": AdaptiveAction.TRUST_REPAIR_MESSAGE in actions,
            "targeted_local_alert_active": (
                AdaptiveAction.TARGETED_LOCAL_ALERT in actions
            ),
            "adaptive_isolation_active": (
                AdaptiveAction.ADAPTIVE_ISOLATION_ENCOURAGEMENT in actions
            ),
        }

    @staticmethod
    def _resolve(
        metric: str,
        target_zone_id: str | None,
        context: dict[str, float],
        zone_risk: dict[str, float],
    ) -> float | None:
        if metric == "zone_risk":
            if target_zone_id is None:
                return max(zone_risk.values(), default=0.0)
            return zone_risk.get(target_zone_id, 0.0)
        return context.get(metric)

    def _apply_effect(self, agent: Agent, intervention: ActiveIntervention) -> None:
        intensity = intervention.intensity
        if intervention.action == AdaptiveAction.COUNTER_MESSAGING:
            agent.safety_rumor_exposure = self._bounded(
                agent.safety_rumor_exposure * (1 - 0.5 * intensity)
            )
            agent.rumor_belief = self._bounded(agent.rumor_belief - 0.02 * intensity)
            agent.rumor_exposure = self._bounded(
                agent.rumor_exposure * (1 - 0.3 * intensity)
            )
        elif intervention.action == AdaptiveAction.PEER_WARNING_CAMPAIGN:
            agent.peer_warning_exposure = self._bounded(
                agent.peer_warning_exposure + 0.05 * intensity
            )
            agent.trust_peers = self._bounded(agent.trust_peers + 0.01 * intensity)
        elif intervention.action == AdaptiveAction.TRUST_REPAIR_MESSAGE:
            agent.trust_authority = self._bounded(
                agent.trust_authority + 0.01 * intensity
            )
            agent.anti_authority_exposure = self._bounded(
                agent.anti_authority_exposure * (1 - 0.3 * intensity)
            )
        elif intervention.action == AdaptiveAction.TARGETED_LOCAL_ALERT:
            boost = 0.04 * intensity
            agent.official_alert_exposure = self._bounded(
                agent.official_alert_exposure + boost
            )
            agent.alert_exposure = self._bounded(agent.alert_exposure + boost)
            agent.local_alert_exposure = self._bounded(
                agent.local_alert_exposure + boost
            )

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
