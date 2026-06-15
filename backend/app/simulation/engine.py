"""Deterministic orchestration for one schedule-based simulation run."""

import random
from dataclasses import dataclass, field
from typing import Any

from app.domain.adaptive import AdaptivePolicy
from app.domain.agent import EpidemiologicalState
from app.domain.behavior_params import BehaviorParameters
from app.domain.disease import DiseaseProfile
from app.domain.information import InformationEvent
from app.domain.policy import Policy
from app.domain.simulation import SimulationSnapshot, SimulationState
from app.domain.time import SimulationTime
from app.domain.world import World
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig
from app.simulation.adaptive import AdaptivePolicyEngine
from app.simulation.behavior import BehaviorEngine
from app.simulation.cognition import CognitionEngine
from app.simulation.contacts import ContactEngine
from app.simulation.information import InformationEngine
from app.simulation.metrics import MetricsEngine
from app.simulation.mobility import MobilityEngine
from app.simulation.policies import PolicyHookEngine
from app.simulation.population import PopulationGenerator
from app.simulation.snapshots import SnapshotBuilder
from app.simulation.social import SocialInfluenceEngine
from app.simulation.transmission import TransmissionEngine


@dataclass(slots=True)
class SimulationEngine:
    """Own mutable state and execute the deterministic Phase 3 tick pipeline."""

    state: SimulationState
    rng: random.Random
    mobility_engine: MobilityEngine = field(default_factory=MobilityEngine)
    contact_engine: ContactEngine = field(default_factory=ContactEngine)
    transmission_engine: TransmissionEngine = field(default_factory=TransmissionEngine)
    information_engine: InformationEngine = field(default_factory=InformationEngine)
    social_engine: SocialInfluenceEngine = field(default_factory=SocialInfluenceEngine)
    cognition_engine: CognitionEngine = field(default_factory=CognitionEngine)
    behavior_engine: BehaviorEngine = field(default_factory=BehaviorEngine)
    adaptive_engine: AdaptivePolicyEngine = field(default_factory=AdaptivePolicyEngine)
    policy_engine: PolicyHookEngine = field(default_factory=PolicyHookEngine)
    metrics_engine: MetricsEngine = field(default_factory=MetricsEngine)
    snapshot_builder: SnapshotBuilder = field(default_factory=SnapshotBuilder)

    @classmethod
    def create(
        cls,
        simulation_id: str,
        world: World,
        disease: DiseaseProfile,
        population_config: AgentPopulationConfig,
        outbreak: InitialOutbreakConfig,
        seed: int,
        policy: Policy | None = None,
        policies: list[Policy] | None = None,
        information_events: list[InformationEvent] | None = None,
        behavior_params: BehaviorParameters | None = None,
        adaptive_policy: AdaptivePolicy | None = None,
        config_summary: dict[str, Any] | None = None,
    ) -> "SimulationEngine":
        agents = PopulationGenerator().generate(
            config=population_config,
            world=world,
            disease=disease,
            outbreak=outbreak,
            seed=seed,
        )
        cumulative = outbreak.exposed_agents + outbreak.infected_agents
        configured_policies = list(policies or [])
        if policy and all(item.id != policy.id for item in configured_policies):
            configured_policies.append(policy)
        configured_events = list(information_events or [])
        state = SimulationState(
            simulation_id=simulation_id,
            seed=seed,
            tick=0,
            world=world,
            disease=disease,
            agents=agents,
            cumulative_infections=cumulative,
            config_summary=config_summary or {},
            policy=policy,
            policies=configured_policies,
            information_events=configured_events,
            behavior_params=behavior_params or BehaviorParameters(),
            adaptive_policy=adaptive_policy,
        )
        engine = cls(state=state, rng=random.Random(seed))
        state.active_policy_ids = [
            item.id for item in configured_policies if item.is_active(0)
        ]
        state.active_information_ids = [
            event.id for event in configured_events if event.is_active(0)
        ]
        state.metrics_history.append(
            engine.metrics_engine.create_snapshot(
                tick=0,
                agents=agents,
                new_infections=0,
                cumulative_infections=cumulative,
                active_policy_count=len(state.active_policy_ids),
                policy_effect_summary={"active_policy_ids": state.active_policy_ids},
            )
        )
        initial_snapshot = engine.snapshot()
        state.snapshots_history.append(engine.snapshot_builder.as_dict(initial_snapshot))
        return engine

    @property
    def simulation_id(self) -> str:
        return self.state.simulation_id

    @property
    def current_step(self) -> int:
        return self.state.tick

    def step(self) -> SimulationSnapshot:
        """Advance schedule, contacts, transmission, metrics, and snapshot once."""

        self.state.tick += 1
        simulation_time = SimulationTime.from_tick(
            self.state.tick,
            self.state.disease.tick_minutes,
        )
        modifiers = self.policy_engine.before_mobility(self.state)
        zone_risk = self._real_risk_by_zone()
        active_adaptive = self.adaptive_engine.evaluate(
            self.state.adaptive_policy,
            self._adaptive_context(),
            zone_risk,
            self.state.tick,
        )
        active_events = tuple(
            event for event in self.state.information_events if event.is_active(self.state.tick)
        )
        information = self.information_engine.step(
            self.state.agents,
            modifiers.active_policies,
            self.state.tick,
            active_events,
        )
        self.state.agents_under_local_alert = information.local_reach
        self.state.agents_under_global_alert = information.global_reach
        self.state.agents_under_rumor = information.rumor_reach
        self.state.active_information_ids = list(information.active_event_ids)
        self.state.information_effect_summary = {
            "active_information_ids": list(information.active_event_ids),
            "official_reach": information.official_reach,
            "rumor_reach": information.rumor_reach,
            "false_safety_reach": information.false_safety_reach,
            "false_danger_reach": information.false_danger_reach,
            "anti_authority_reach": information.anti_authority_reach,
        }
        social = self.social_engine.step(
            self.state.agents,
            tuple(self.state.world.zones),
            self.state.tick,
        )
        self.state.zone_social_pressures = social.zone_pressures
        self.state.rumor_pressure = social.mean_rumor_pressure
        self.state.peer_warning_pressure = social.mean_peer_warning_pressure
        self.adaptive_engine.apply(self.state.agents, self.state.tick)
        self.transmission_engine.progress(
            self.state.agents,
            self.state.disease,
            self.state.tick,
            self.rng,
        )
        isolated_this_tick = self.policy_engine.apply_isolation(self.state, modifiers)
        isolated_this_tick += self.adaptive_engine.apply_adaptive_isolation(
            self.state.agents, self.state.tick
        )
        self._record_adaptive_state()
        self.cognition_engine.step(
            self.state.agents,
            zone_risk,
            modifiers,
            self.state.tick,
        )
        self.behavior_engine.step(
            self.state.agents, modifiers, self.state.tick, self.state.behavior_params
        )
        movement = self.mobility_engine.step(
            self.state.agents,
            self.state.world,
            simulation_time,
            self.rng,
            modifiers,
        )
        self.state.movement_reduction_estimate = (
            movement.policy_blocked / movement.attempted if movement.attempted else 0.0
        )
        self.policy_engine.before_contacts(self.state)
        contact_batch = self.contact_engine.step(
            self.state.agents,
            self.state.world,
            self.state.tick,
            self.state.disease.tick_minutes,
            modifiers,
            self.state.behavior_params,
        )
        # Policy-only reduction keeps its Phase 3 meaning; behavior is tracked
        # separately via raw vs effective contact counts.
        self.state.contact_reduction_estimate = (
            1 - contact_batch.policy_contact_count / contact_batch.raw_contact_count
            if contact_batch.raw_contact_count
            else 0.0
        )
        self.state.raw_contact_count = contact_batch.raw_contact_count
        self.state.effective_contact_count = contact_batch.effective_contact_count
        self.state.policy_effect_summary.update(
            {
                "isolated_this_tick": isolated_this_tick,
                "movement_attempts": movement.attempted,
                "movements_prevented": movement.policy_blocked,
                "raw_contacts": contact_batch.raw_contact_count,
                "policy_contacts": contact_batch.policy_contact_count,
                "effective_contacts": contact_batch.effective_contact_count,
            }
        )
        self.policy_engine.before_transmission(self.state)
        transmission = self.transmission_engine.transmit(
            contact_batch,
            self.state.world,
            self.state.disease,
            self.state.tick,
            self.rng,
            modifiers,
            self.state.behavior_params,
        )
        infections_by_zone = transmission.infections_by_zone
        self.state.effective_beta_mean = transmission.effective_beta_mean
        self.state.behavioral_transmission_reduction = (
            transmission.behavioral_transmission_reduction
        )
        self.state.misinformation_transmission_amplification = (
            transmission.misinformation_transmission_amplification
        )
        for record in contact_batch.records:
            record.new_infections = infections_by_zone.get(record.zone_id, 0)
        self.state.contact_history.extend(contact_batch.records)

        new_infections = sum(infections_by_zone.values())
        self.state.new_infections = new_infections
        self.state.cumulative_infections += new_infections
        self.state.metrics_history.append(
            self.metrics_engine.create_snapshot(
                tick=self.state.tick,
                agents=self.state.agents,
                new_infections=new_infections,
                cumulative_infections=self.state.cumulative_infections,
                active_policy_count=len(self.state.active_policy_ids),
                agents_under_local_alert=self.state.agents_under_local_alert,
                agents_under_global_alert=self.state.agents_under_global_alert,
                contact_count=contact_batch.effective_contact_count,
                movement_reduction_estimate=self.state.movement_reduction_estimate,
                contact_reduction_estimate=self.state.contact_reduction_estimate,
                raw_contact_count=contact_batch.raw_contact_count,
                effective_contact_count=contact_batch.effective_contact_count,
                effective_beta_mean=transmission.effective_beta_mean,
                behavioral_transmission_reduction=transmission.behavioral_transmission_reduction,
                misinformation_transmission_amplification=transmission.misinformation_transmission_amplification,
                rumor_pressure=social.mean_rumor_pressure,
                peer_warning_pressure=social.mean_peer_warning_pressure,
                adaptive_policy_trigger_count=self.state.adaptive_policy_trigger_count,
                adaptive_policy_active_count=self.state.adaptive_policy_active_count,
                counter_messaging_active=self.state.counter_messaging_active,
                peer_warning_campaign_active=self.state.peer_warning_campaign_active,
                trust_repair_active=self.state.trust_repair_active,
                adaptive_isolation_active=self.state.adaptive_isolation_active,
                last_triggered_adaptive_rule=self.state.last_triggered_adaptive_rule,
                policy_effect_summary=self.state.policy_effect_summary.copy(),
                adaptive_policy_effect_summary=self.state.adaptive_policy_effect_summary.copy(),
            )
        )
        self.policy_engine.after_metrics(self.state)
        snapshot = self.snapshot()
        self.state.snapshots_history.append(self.snapshot_builder.as_dict(snapshot))
        return snapshot

    def run(self, ticks: int) -> SimulationSnapshot:
        if ticks <= 0:
            raise ValueError("ticks must be greater than zero")
        for _ in range(ticks):
            self.step()
        return self.snapshot()

    def _adaptive_context(self) -> dict[str, float]:
        """Build the metric context adaptive rules evaluate, from prior metrics."""

        history = self.state.metrics_history
        if not history:
            return {}
        latest = history[-1]
        context = {
            "misinformation_transmission_amplification": (
                latest.misinformation_transmission_amplification
            ),
            "behavioral_transmission_reduction": latest.behavioral_transmission_reduction,
            "effective_beta_mean": latest.effective_beta_mean,
            "mean_trust_authority": latest.mean_trust_authority,
            "mean_protection_behavior": latest.mean_protection_behavior,
            "mean_perceived_risk": latest.mean_perceived_risk,
            "mean_rumor_exposure": latest.mean_rumor_exposure,
            "active_infections": float(latest.active_infections),
            "new_infections": float(latest.new_infections),
            "cumulative_infections": float(latest.cumulative_infections),
        }
        if len(history) >= 2:
            context["active_infections_trend"] = float(
                latest.active_infections - history[-2].active_infections
            )
        else:
            context["active_infections_trend"] = 0.0
        return context

    def _record_adaptive_state(self) -> None:
        """Mirror the adaptive engine's live state onto the simulation state."""

        summary = self.adaptive_engine.effect_summary()
        self.state.adaptive_policy_trigger_count = self.adaptive_engine.trigger_count
        self.state.adaptive_policy_active_count = len(self.adaptive_engine.active)
        self.state.counter_messaging_active = summary["counter_messaging_active"]
        self.state.peer_warning_campaign_active = summary["peer_warning_campaign_active"]
        self.state.trust_repair_active = summary["trust_repair_active"]
        self.state.adaptive_isolation_active = summary["adaptive_isolation_active"]
        self.state.last_triggered_adaptive_rule = self.adaptive_engine.last_triggered_rule
        self.state.adaptive_policy_effect_summary = summary

    def _real_risk_by_zone(self) -> dict[str, float]:
        """Local active-infection ratio per zone, used as objective real risk."""

        population: dict[str, int] = {zone_id: 0 for zone_id in self.state.world.zones}
        active: dict[str, int] = {zone_id: 0 for zone_id in self.state.world.zones}
        active_states = {
            EpidemiologicalState.EXPOSED,
            EpidemiologicalState.INFECTED_ASYMPTOMATIC,
            EpidemiologicalState.INFECTED_SYMPTOMATIC,
            EpidemiologicalState.ISOLATED,
        }
        for agent in self.state.agents:
            population[agent.zone_id] += 1
            if agent.state in active_states:
                active[agent.zone_id] += 1
        return {
            zone_id: (active[zone_id] / population[zone_id] if population[zone_id] else 0.0)
            for zone_id in population
        }

    def snapshot(self) -> SimulationSnapshot:
        return self.snapshot_builder.create_snapshot(self.state)

    def create_snapshot(self) -> dict[str, object]:
        return self.snapshot_builder.as_dict(self.snapshot())
