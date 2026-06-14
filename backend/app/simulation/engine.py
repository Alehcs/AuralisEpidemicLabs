"""Deterministic orchestration for one schedule-based simulation run."""

import random
from dataclasses import dataclass, field
from typing import Any

from app.domain.disease import DiseaseProfile
from app.domain.policy import Policy
from app.domain.simulation import SimulationSnapshot, SimulationState
from app.domain.time import SimulationTime
from app.domain.world import World
from app.schemas.configs import AgentPopulationConfig, InitialOutbreakConfig
from app.simulation.contacts import ContactEngine
from app.simulation.information import InformationEngine
from app.simulation.metrics import MetricsEngine
from app.simulation.mobility import MobilityEngine
from app.simulation.policies import PolicyHookEngine
from app.simulation.population import PopulationGenerator
from app.simulation.snapshots import SnapshotBuilder
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
        )
        engine = cls(state=state, rng=random.Random(seed))
        state.active_policy_ids = [
            item.id for item in configured_policies if item.is_active(0)
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
        information = self.information_engine.step(
            self.state.agents,
            modifiers.active_policies,
            self.state.tick,
        )
        self.state.agents_under_local_alert = information.local_reach
        self.state.agents_under_global_alert = information.global_reach
        self.transmission_engine.progress(
            self.state.agents,
            self.state.disease,
            self.state.tick,
            self.rng,
        )
        isolated_this_tick = self.policy_engine.apply_isolation(self.state, modifiers)
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
        self.state.contact_reduction_estimate = (
            1 - contact_batch.effective_contact_count / contact_batch.baseline_contact_count
            if contact_batch.baseline_contact_count
            else 0.0
        )
        self.state.policy_effect_summary.update(
            {
                "isolated_this_tick": isolated_this_tick,
                "movement_attempts": movement.attempted,
                "movements_prevented": movement.policy_blocked,
                "baseline_contacts": contact_batch.baseline_contact_count,
                "effective_contacts": contact_batch.effective_contact_count,
            }
        )
        self.policy_engine.before_transmission(self.state)
        infections_by_zone = self.transmission_engine.transmit(
            contact_batch,
            self.state.world,
            self.state.disease,
            self.state.tick,
            self.rng,
            modifiers,
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

    def snapshot(self) -> SimulationSnapshot:
        return self.snapshot_builder.create_snapshot(self.state)

    def create_snapshot(self) -> dict[str, object]:
        return self.snapshot_builder.as_dict(self.snapshot())
