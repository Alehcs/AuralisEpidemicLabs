"""Policy activation, intervention modifiers, and lifecycle hooks."""

from dataclasses import dataclass, field

from app.domain.agent import EpidemiologicalState
from app.domain.policy import Policy, PolicyType
from app.domain.simulation import SimulationState


@dataclass(frozen=True, slots=True)
class PolicyModifiers:
    """Bounded multipliers consumed by independent simulation engines."""

    active_policies: tuple[Policy, ...] = ()
    zone_mobility: dict[str, float] = field(default_factory=dict)
    zone_contacts: dict[str, float] = field(default_factory=dict)
    zone_transmission: dict[str, float] = field(default_factory=dict)
    closed_zones: frozenset[str] = frozenset()

    def mobility_multiplier(self, zone_id: str) -> float:
        return self.zone_mobility.get(zone_id, 1.0)

    def contact_multiplier(self, zone_id: str) -> float:
        return self.zone_contacts.get(zone_id, 1.0)

    def transmission_multiplier(self, zone_id: str) -> float:
        return self.zone_transmission.get(zone_id, 1.0)


@dataclass(slots=True)
class PolicyHookEngine:
    """Resolve scheduled policies into deterministic Phase 3 effects."""

    hook_history: list[tuple[int, str, str]] = field(default_factory=list)

    def before_mobility(self, state: SimulationState) -> PolicyModifiers:
        active = self._active_policies(state)
        self._record(state, "before_mobility", active)
        return self._build_modifiers(state, active)

    def before_contacts(self, state: SimulationState) -> None:
        self._record(state, "before_contacts", self._active_policies(state))

    def before_transmission(self, state: SimulationState) -> None:
        self._record(state, "before_transmission", self._active_policies(state))

    def after_metrics(self, state: SimulationState) -> None:
        self._record(state, "after_metrics", self._active_policies(state))

    def apply_isolation(self, state: SimulationState, modifiers: PolicyModifiers) -> int:
        """Isolate compliant symptomatic agents while preserving recovery timing."""

        policies = [
            policy
            for policy in modifiers.active_policies
            if policy.policy_type == PolicyType.ISOLATION_ENCOURAGEMENT
        ]
        isolated = 0
        for policy in policies:
            threshold = max(0.0, policy.compliance_requirement - policy.intensity * 0.2)
            for agent in state.agents:
                if (
                    agent.state == EpidemiologicalState.INFECTED_SYMPTOMATIC
                    and agent.isolation_compliance >= threshold
                ):
                    agent.pre_isolation_state = agent.state
                    agent.state = EpidemiologicalState.ISOLATED
                    agent.isolation_started_tick = state.tick
                    isolated += 1
        return isolated

    def _active_policies(self, state: SimulationState) -> tuple[Policy, ...]:
        policies = state.policies or ([state.policy] if state.policy else [])
        return tuple(policy for policy in policies if policy.is_active(state.tick))

    def _record(
        self,
        state: SimulationState,
        hook: str,
        active: tuple[Policy, ...],
    ) -> None:
        state.active_policy_ids = [policy.id for policy in active]
        self.hook_history.extend((state.tick, hook, policy.id) for policy in active)

    def _build_modifiers(
        self,
        state: SimulationState,
        active: tuple[Policy, ...],
    ) -> PolicyModifiers:
        zone_mobility = {zone_id: 1.0 for zone_id in state.world.zones}
        zone_contacts = {zone_id: 1.0 for zone_id in state.world.zones}
        zone_transmission = {zone_id: 1.0 for zone_id in state.world.zones}
        closed_zones: set[str] = set()

        for policy in active:
            targets = (
                list(state.world.zones)
                if policy.scope == "global"
                else [policy.target_zone_id] if policy.target_zone_id else []
            )
            for zone_id in targets:
                zone_mobility[zone_id] *= 1 - policy.intensity * policy.mobility_impact
                zone_contacts[zone_id] *= 1 - policy.intensity * policy.contact_impact
                zone_transmission[zone_id] *= 1 - policy.intensity * policy.transmission_impact
            if policy.policy_type == PolicyType.ZONE_CLOSURE and policy.target_zone_id:
                closed_zones.add(policy.target_zone_id)

        zone_mobility = {key: round(max(0.02, value), 6) for key, value in zone_mobility.items()}
        zone_contacts = {key: round(max(0.05, value), 6) for key, value in zone_contacts.items()}
        zone_transmission = {
            key: round(max(0.05, value), 6) for key, value in zone_transmission.items()
        }
        state.policy_effect_summary = {
            "active_policy_ids": [policy.id for policy in active],
            "closed_zones": sorted(closed_zones),
            "mean_mobility_multiplier": round(sum(zone_mobility.values()) / len(zone_mobility), 6),
            "mean_contact_multiplier": round(sum(zone_contacts.values()) / len(zone_contacts), 6),
            "mean_transmission_multiplier": round(
                sum(zone_transmission.values()) / len(zone_transmission), 6
            ),
        }
        return PolicyModifiers(
            active_policies=active,
            zone_mobility=zone_mobility,
            zone_contacts=zone_contacts,
            zone_transmission=zone_transmission,
            closed_zones=frozenset(closed_zones),
        )
