"""Interactive simulation lifecycle endpoints."""

from fastapi import APIRouter

from app.application.simulation_service import SimulationService
from app.schemas.simulation import SimulationCreateRequest, SimulationStateResponse

router = APIRouter(prefix="/simulations", tags=["simulations"])
service = SimulationService()


@router.post("/create", response_model=SimulationStateResponse, status_code=201)
def create_simulation(request: SimulationCreateRequest) -> SimulationStateResponse:
    """Create an in-memory Phase 0 simulation placeholder."""

    return service.create(request)


@router.post("/{simulation_id}/step", response_model=SimulationStateResponse)
def step_simulation(simulation_id: str) -> SimulationStateResponse:
    """Advance an existing placeholder simulation by one tick."""

    return service.step(simulation_id)


@router.get("/{simulation_id}/state", response_model=SimulationStateResponse)
def simulation_state(simulation_id: str) -> SimulationStateResponse:
    """Read an existing placeholder simulation state."""

    return service.state(simulation_id)
