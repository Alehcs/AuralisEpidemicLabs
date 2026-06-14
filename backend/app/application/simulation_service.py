"""Interactive in-memory simulation lifecycle use cases."""

from dataclasses import asdict
from uuid import uuid4

from app.core.errors import ConfigValidationError, SimulationNotFoundError
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import RunExporter
from app.schemas.simulation import (
    MetricsSnapshotResponse,
    SimulationCreateRequest,
    ExportRunResponse,
    SimulationMetricsResponse,
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
        policy_config = self.loader.load_policy(request.policy_config) if request.policy_config else None

        simulation_id = str(uuid4())
        try:
            engine = SimulationEngine.create(
                simulation_id=simulation_id,
                world=self.loader.to_world(scenario),
                disease=self.loader.to_disease(disease_config),
                population_config=population,
                outbreak=scenario.initial_outbreak,
                seed=request.seed,
                policy=self.loader.to_policy(policy_config) if policy_config else None,
                config_summary={
                    "scenario_config": request.scenario_config,
                    "disease_config": request.disease_config,
                    "population_config": request.population_config,
                    "policy_config": request.policy_config,
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
