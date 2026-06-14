"""Interactive simulation lifecycle use cases."""

from uuid import uuid4

from app.core.errors import SimulationNotFoundError
from app.schemas.simulation import SimulationCreateRequest, SimulationStateResponse
from app.simulation.engine import SimulationEngine


class SimulationService:
    """Manage Phase 0 engines in memory behind an application boundary."""

    def __init__(self) -> None:
        self._engines: dict[str, SimulationEngine] = {}

    def create(self, request: SimulationCreateRequest) -> SimulationStateResponse:
        """Create a placeholder engine carrying references to requested configs."""

        simulation_id = str(uuid4())
        engine = SimulationEngine(simulation_id=simulation_id, metadata=request.model_dump())
        self._engines[simulation_id] = engine
        return self._response(engine, "Simulation created; ABM behavior is not implemented in Phase 0.")

    def step(self, simulation_id: str) -> SimulationStateResponse:
        """Advance one placeholder step."""

        engine = self._get_engine(simulation_id)
        engine.step()
        return self._response(engine, "Placeholder simulation advanced by one step.")

    def state(self, simulation_id: str) -> SimulationStateResponse:
        """Read the current placeholder state."""

        engine = self._get_engine(simulation_id)
        return self._response(engine, "Current Phase 0 simulation state.")

    def _get_engine(self, simulation_id: str) -> SimulationEngine:
        try:
            return self._engines[simulation_id]
        except KeyError as error:
            raise SimulationNotFoundError(f"Simulation not found: {simulation_id}") from error

    @staticmethod
    def _response(engine: SimulationEngine, message: str) -> SimulationStateResponse:
        return SimulationStateResponse(
            simulation_id=engine.simulation_id,
            status="placeholder",
            current_step=engine.current_step,
            message=message,
            snapshot=engine.create_snapshot(),
        )
