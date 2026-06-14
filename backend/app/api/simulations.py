"""Interactive simulation lifecycle endpoints."""

from fastapi import APIRouter

from app.application.simulation_service import SimulationService
from app.core.settings import get_settings
from app.infrastructure.config_loader import ConfigLoader
from app.schemas.simulation import (
    SimulationCreateRequest,
    SimulationMetricsResponse,
    SimulationRunRequest,
    SimulationStateResponse,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])
service = SimulationService(ConfigLoader(get_settings().config_directory))


@router.post("/create", response_model=SimulationStateResponse, status_code=201)
def create_simulation(request: SimulationCreateRequest) -> SimulationStateResponse:
    """Create an in-memory deterministic simulation."""

    return service.create(request)


@router.post("/{simulation_id}/step", response_model=SimulationStateResponse)
def step_simulation(simulation_id: str) -> SimulationStateResponse:
    """Advance an existing simulation by one tick."""

    return service.step(simulation_id)


@router.post("/{simulation_id}/run", response_model=SimulationStateResponse)
def run_simulation(
    simulation_id: str,
    request: SimulationRunRequest,
) -> SimulationStateResponse:
    """Advance an existing simulation by a bounded number of ticks."""

    return service.run(simulation_id, request.ticks)


@router.get("/{simulation_id}/state", response_model=SimulationStateResponse)
def simulation_state(simulation_id: str) -> SimulationStateResponse:
    """Read an existing simulation state."""

    return service.state(simulation_id)


@router.get("/{simulation_id}/metrics", response_model=SimulationMetricsResponse)
def simulation_metrics(simulation_id: str) -> SimulationMetricsResponse:
    """Read metric history accumulated by a simulation."""

    return service.metrics(simulation_id)
