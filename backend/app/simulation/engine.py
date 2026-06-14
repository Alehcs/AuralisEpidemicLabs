"""Deterministic orchestration for one schedule-based simulation run."""

import random
from dataclasses import dataclass, field
from typing import Any

from app.domain.agent import EpidemiologicalState
from app.domain.disease import DiseaseProfile
from app.domain.information import InformationEvent
from app.domain.policy import Policy
from app.domain.simulation import SimulationSnapshot, SimulationState
from app.domain.time import SimulationTime
from app.domain.world import World
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig
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
        self.transmission_engine.progress(
            self.state.agents,
            self.state.disease,
            self.state.tick,
            self.rng,
        )
        isolated_this_tick = self.policy_engine.apply_isolation(self.state, modifiers)
        self.cognition_engine.step(
            self.state.agents,
            self._real_risk_by_zone(),
            modifiers,
            self.state.tick,
        )
        self.behavior_engine.step(self.state.agents, modifiers, self.state.tick)
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
                policy_effect_summary=self.state.policy_effect_summary.copy(),
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
