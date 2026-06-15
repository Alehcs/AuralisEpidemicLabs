"""Interactive in-memory simulation lifecycle use cases."""

from dataclasses import asdict
from uuid import uuid4

from app.core.errors import ConfigValidationError, SimulationNotFoundError
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import RunExporter
from app.schemas.simulation import (
    MetricsSnapshotResponse,
    SimulationAdaptiveResponse,
    SimulationBehaviorResponse,
    SimulationCognitionResponse,
    SimulationCreateRequest,
    ExportRunResponse,
    SimulationInformationResponse,
    SimulationMetricsResponse,
    SimulationPoliciesResponse,
    SimulationSocialResponse,
    SimulationStateResponse,
    SimulationSnapshotResponse,
)
from app.simulation.engine import SimulationEngine


class SimulationService:
    """Create and manage deterministic engines in process memory."""

    def __init__(self, loader: ConfigLoader, exporter: RunExporter) -> None:
        self.loader = loader
        self.exporter = exporter
        self._engines: dict[str, SimulationEngine] = {}

    def create(self, request: SimulationCreateRequest) -> SimulationStateResponse:
        """Validate configs, convert domain inputs, and create a real engine."""

        scenario = self.loader.load_scenario(request.scenario_config)
        disease_config = self.loader.load_disease(request.disease_config)
        population = self.loader.load_population(request.population_config)
        policy_names = request.policy_configs or (
            [request.policy_config] if request.policy_config else []
        )
        policy_configs = [self.loader.load_policy(name) for name in policy_names]
        policies = [self.loader.to_policy(config) for config in policy_configs]
        information_events = [
            self.loader.to_information_event(self.loader.load_information(name))
            for name in request.information_configs
        ]
        behavior_params = (
            self.loader.to_behavior_parameters(
                self.loader.load_behavior(request.behavior_config)
            )
            if request.behavior_config
            else None
        )
        adaptive_policy = (
            self.loader.to_adaptive_policy(
                self.loader.load_adaptive(request.adaptive_policy_config)
            )
            if request.adaptive_policy_config
            else None
        )

        simulation_id = str(uuid4())
        try:
            engine = SimulationEngine.create(
                simulation_id=simulation_id,
                world=self.loader.to_world(scenario),
                disease=self.loader.to_disease(disease_config),
                population_config=population,
                outbreak=scenario.initial_outbreak,
                seed=request.seed,
                policy=policies[0] if len(policies) == 1 else None,
                policies=policies,
                information_events=information_events,
                behavior_params=behavior_params,
                adaptive_policy=adaptive_policy,
                config_summary={
                    "scenario_config": request.scenario_config,
                    "disease_config": request.disease_config,
                    "population_config": request.population_config,
                    "policy_config": request.policy_config,
                    "policy_configs": policy_names,
                    "information_configs": request.information_configs,
                    "behavior_config": request.behavior_config,
                    "adaptive_policy_config": request.adaptive_policy_config,
                    "seed": request.seed,
                },
            )
        except ValueError as error:
            raise ConfigValidationError(str(error)) from error
        self._engines[simulation_id] = engine
        return self._response(engine, "Simulation created from validated configs.")

    def step(self, simulation_id: str) -> SimulationStateResponse:
        """Advance one deterministic simulation tick."""

        engine = self._get_engine(simulation_id)
        engine.step()
        return self._response(engine, "Simulation advanced by one tick.")

    def run(self, simulation_id: str, ticks: int) -> SimulationStateResponse:
        """Advance multiple ticks synchronously."""

        engine = self._get_engine(simulation_id)
        engine.run(ticks)
        return self._response(engine, f"Simulation advanced by {ticks} ticks.")

    def state(self, simulation_id: str) -> SimulationStateResponse:
        """Read the current state without consuming random values."""

        return self._response(self._get_engine(simulation_id), "Current simulation state.")

    def metrics(self, simulation_id: str) -> SimulationMetricsResponse:
        """Return the complete metric history for charting."""

        engine = self._get_engine(simulation_id)
        return SimulationMetricsResponse(
            simulation_id=simulation_id,
            history=[MetricsSnapshotResponse.model_validate(asdict(item)) for item in engine.state.metrics_history],
        )

    def policies(self, simulation_id: str) -> SimulationPoliciesResponse:
        """Return configured policies and their current activation state."""

        engine = self._get_engine(simulation_id)
        policies = engine.state.policies or (
            [engine.state.policy] if engine.state.policy else []
        )
        return SimulationPoliciesResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": engine.state.tick,
                "configured": [
                    {
                        "id": policy.id,
                        "name": policy.name,
                        "type": policy.policy_type.value,
                        "scope": policy.scope,
                        "target_zone_id": policy.target_zone_id,
                        "active": policy.is_active(engine.state.tick),
                        "start_tick": policy.start_tick,
                        "end_tick": policy.end_tick,
                        "intensity": policy.intensity,
                    }
                    for policy in policies
                ],
                "active_policy_ids": engine.state.active_policy_ids,
                "effect_summary": engine.state.policy_effect_summary,
            }
        )

    def cognition(self, simulation_id: str) -> SimulationCognitionResponse:
        """Return current cognitive aggregates and a bounded agent sample."""

        engine = self._get_engine(simulation_id)
        metrics = engine.state.metrics_history[-1]
        snapshot = engine.snapshot()
        return SimulationCognitionResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": engine.state.tick,
                "metrics": {
                    "mean_perceived_risk": metrics.mean_perceived_risk,
                    "mean_real_risk": metrics.mean_real_risk,
                    "mean_perception_gap": metrics.mean_perception_gap,
                    "mean_trust_authority": metrics.mean_trust_authority,
                    "mean_trust_peers": metrics.mean_trust_peers,
                    "mean_fatigue": metrics.mean_fatigue,
                    "mean_fear": metrics.mean_fear,
                    "mean_curiosity": metrics.mean_curiosity,
                    "mean_compliance": metrics.mean_compliance,
                    "mean_rumor_belief": metrics.mean_rumor_belief,
                },
                "sample_agents": snapshot.sample_agents_for_visualization,
            }
        )

    def information(self, simulation_id: str) -> SimulationInformationResponse:
        """Return configured information events and current exposure reach."""

        engine = self._get_engine(simulation_id)
        state = engine.state
        metrics = state.metrics_history[-1]
        return SimulationInformationResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": state.tick,
                "events": [
                    {
                        "id": event.id,
                        "event_type": event.event_type.value,
                        "source": event.source,
                        "scope": "global" if event.is_global else "local",
                        "target_zone_id": event.target_zone_id,
                        "active": event.is_active(state.tick),
                        "start_tick": event.start_tick,
                        "end_tick": event.end_tick,
                        "intensity": event.intensity,
                        "reach": event.reach,
                        "accuracy": event.accuracy,
                    }
                    for event in state.information_events
                ],
                "active_information_ids": state.active_information_ids,
                "exposure": {
                    "agents_under_local_alert": state.agents_under_local_alert,
                    "agents_under_global_alert": state.agents_under_global_alert,
                    "agents_under_rumor": state.agents_under_rumor,
                    "rumor_exposure_count": metrics.rumor_exposure_count,
                    "official_alert_exposure_count": metrics.official_alert_exposure_count,
                    "false_safety_exposure_count": metrics.false_safety_exposure_count,
                    "anti_authority_exposure_count": metrics.anti_authority_exposure_count,
                },
                "effect_summary": state.information_effect_summary,
            }
        )

    def behavior(self, simulation_id: str) -> SimulationBehaviorResponse:
        """Return behavior aggregates and a bounded agent sample."""

        engine = self._get_engine(simulation_id)
        metrics = engine.state.metrics_history[-1]
        snapshot = engine.snapshot()
        return SimulationBehaviorResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": engine.state.tick,
                "metrics": {
                    "mean_protection_behavior": metrics.mean_protection_behavior,
                    "mean_distancing_behavior": metrics.mean_distancing_behavior,
                    "mean_risk_compensation": metrics.mean_risk_compensation,
                    "mean_risky_optional_movement_bias": metrics.mean_risky_optional_movement_bias,
                    "raw_contact_count": metrics.raw_contact_count,
                    "effective_contact_count": metrics.effective_contact_count,
                    "effective_beta_mean": metrics.effective_beta_mean,
                    "behavioral_transmission_reduction": metrics.behavioral_transmission_reduction,
                    "misinformation_transmission_amplification": (
                        metrics.misinformation_transmission_amplification
                    ),
                },
                "sample_agents": snapshot.sample_agents_for_visualization,
            }
        )

    def social(self, simulation_id: str) -> SimulationSocialResponse:
        """Return district-wide and per-zone social-influence pressures."""

        engine = self._get_engine(simulation_id)
        state = engine.state
        metrics = state.metrics_history[-1]
        return SimulationSocialResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": state.tick,
                "mean_rumor_pressure": state.rumor_pressure,
                "mean_peer_warning_pressure": state.peer_warning_pressure,
                "mean_peer_rumor_exposure": metrics.mean_peer_rumor_exposure,
                "mean_peer_warning_exposure": metrics.mean_peer_warning_exposure,
                "zone_pressures": state.zone_social_pressures,
            }
        )

    def adaptive_policies(self, simulation_id: str) -> SimulationAdaptiveResponse:
        """Return configured adaptive rules and live intervention state."""

        engine = self._get_engine(simulation_id)
        state = engine.state
        policy = state.adaptive_policy
        return SimulationAdaptiveResponse.model_validate(
            {
                "simulation_id": simulation_id,
                "tick": state.tick,
                "policy_id": policy.id if policy else None,
                "rules": [
                    {
                        "id": rule.id,
                        "metric": rule.metric,
                        "operator": rule.operator,
                        "threshold": rule.threshold,
                        "action": rule.action.value,
                        "target": rule.target,
                        "target_zone_id": rule.target_zone_id,
                        "duration_ticks": rule.duration_ticks,
                        "intensity": rule.intensity,
                        "cooldown_ticks": rule.cooldown_ticks,
                    }
                    for rule in (policy.rules if policy else ())
                ],
                "active_interventions": [
                    {
                        "rule_id": item.rule_id,
                        "action": item.action.value,
                        "target": item.target,
                        "target_zone_id": item.target_zone_id,
                        "intensity": item.intensity,
                        "start_tick": item.start_tick,
                        "end_tick": item.end_tick,
                    }
                    for item in engine.adaptive_engine.active
                ],
                "trigger_count": engine.adaptive_engine.trigger_count,
                "last_triggered_rule": engine.adaptive_engine.last_triggered_rule,
                "effect_summary": state.adaptive_policy_effect_summary,
            }
        )

    def export(self, simulation_id: str) -> ExportRunResponse:
        """Persist a deterministic local bundle for an in-memory simulation."""

        engine = self._get_engine(simulation_id)
        return ExportRunResponse.model_validate(self.exporter.export(engine.state))

    def _get_engine(self, simulation_id: str) -> SimulationEngine:
        try:
            return self._engines[simulation_id]
        except KeyError as error:
            raise SimulationNotFoundError(f"Simulation not found: {simulation_id}") from error

    @staticmethod
    def _response(engine: SimulationEngine, message: str) -> SimulationStateResponse:
        snapshot = SimulationSnapshotResponse.model_validate(asdict(engine.snapshot()))
        return SimulationStateResponse(
            simulation_id=engine.simulation_id,
            status="ready",
            current_step=engine.current_step,
            message=message,
            snapshot=snapshot,
        )
