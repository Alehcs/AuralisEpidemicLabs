"""Interactive simulation lifecycle endpoints."""

from fastapi import APIRouter

from app.application.simulation_service import SimulationService
from app.core.settings import get_settings
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.exporters import RunExporter
from app.schemas.simulation import (
    ExportRunResponse,
    SimulationAdaptiveResponse,
    SimulationBehaviorResponse,
    SimulationCognitionResponse,
    SimulationCreateRequest,
    SimulationInformationResponse,
    SimulationMetricsResponse,
    SimulationPoliciesResponse,
    SimulationRunRequest,
    SimulationSocialResponse,
    SimulationStateResponse,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])
settings = get_settings()
service = SimulationService(
    ConfigLoader(settings.config_directory),
    RunExporter(settings.output_directory),
)


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


@router.get("/{simulation_id}/policies", response_model=SimulationPoliciesResponse)
def simulation_policies(simulation_id: str) -> SimulationPoliciesResponse:
    """Read configured policies and current intervention effects."""

    return service.policies(simulation_id)


@router.get("/{simulation_id}/cognition", response_model=SimulationCognitionResponse)
def simulation_cognition(simulation_id: str) -> SimulationCognitionResponse:
    """Read current socio-cognitive aggregates and a bounded agent sample."""

    return service.cognition(simulation_id)


@router.get("/{simulation_id}/information", response_model=SimulationInformationResponse)
def simulation_information(simulation_id: str) -> SimulationInformationResponse:
    """Read configured information events and current exposure reach."""

    return service.information(simulation_id)


@router.get("/{simulation_id}/behavior", response_model=SimulationBehaviorResponse)
def simulation_behavior(simulation_id: str) -> SimulationBehaviorResponse:
    """Read behavior aggregates and transmission-feedback effects."""

    return service.behavior(simulation_id)


@router.get("/{simulation_id}/social", response_model=SimulationSocialResponse)
def simulation_social(simulation_id: str) -> SimulationSocialResponse:
    """Read district-wide and per-zone social-influence pressures."""

    return service.social(simulation_id)


@router.get("/{simulation_id}/adaptive-policies", response_model=SimulationAdaptiveResponse)
def simulation_adaptive_policies(simulation_id: str) -> SimulationAdaptiveResponse:
    """Read configured adaptive rules and live adaptive intervention state."""

    return service.adaptive_policies(simulation_id)


@router.post("/{simulation_id}/export", response_model=ExportRunResponse)
def export_simulation(simulation_id: str) -> ExportRunResponse:
    """Export metadata, metrics, compact snapshots, and final summary."""

    return service.export(simulation_id)
