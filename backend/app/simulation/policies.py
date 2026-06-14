"""Scheduled policy lifecycle hooks for future intervention effects."""

from dataclasses import dataclass, field

from app.domain.simulation import SimulationState


@dataclass(slots=True)
class PolicyHookEngine:
    """Expose stable intervention hook points without applying effects yet.

    TODO Phase 3+: policy strategies may alter mobility, contacts, transmission,
    isolation incentives, alerts, or information after explicit model design.
    """

    hook_history: list[tuple[int, str, str]] = field(default_factory=list)

    def before_mobility(self, state: SimulationState) -> None:
        self._record(state, "before_mobility")

    def before_contacts(self, state: SimulationState) -> None:
        self._record(state, "before_contacts")

    def before_transmission(self, state: SimulationState) -> None:
        self._record(state, "before_transmission")

    def after_metrics(self, state: SimulationState) -> None:
        self._record(state, "after_metrics")

    def _record(self, state: SimulationState, hook: str) -> None:
        policy = state.policy
        state.active_policy_ids = [policy.id] if policy and policy.is_active(state.tick) else []
        if policy and policy.is_active(state.tick):
            self.hook_history.append((state.tick, hook, policy.id))
