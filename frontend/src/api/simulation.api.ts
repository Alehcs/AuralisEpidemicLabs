import { apiGet, apiPost } from "./client";
import type {
  SimulationCreateRequest,
  ExperimentResultResponse,
  ExportRunResponse,
  SimulationMetricsResponse,
  SimulationStateResponse,
  SweepResultResponse,
} from "../types/simulation";

export function createSimulation(
  request: SimulationCreateRequest,
): Promise<SimulationStateResponse> {
  return apiPost<SimulationStateResponse>("/simulations/create", request);
}

export function stepSimulation(simulationId: string): Promise<SimulationStateResponse> {
  return apiPost<SimulationStateResponse>(`/simulations/${simulationId}/step`);
}

export function runSimulation(
  simulationId: string,
  ticks: number,
): Promise<SimulationStateResponse> {
  return apiPost<SimulationStateResponse>(`/simulations/${simulationId}/run`, { ticks });
}

export function getSimulationMetrics(
  simulationId: string,
): Promise<SimulationMetricsResponse> {
  return apiGet<SimulationMetricsResponse>(`/simulations/${simulationId}/metrics`);
}

export function exportSimulation(simulationId: string): Promise<ExportRunResponse> {
  return apiPost<ExportRunResponse>(`/simulations/${simulationId}/export`);
}

export function runBatchExperiment(
  experimentConfig = "global_vs_local_alert",
): Promise<ExperimentResultResponse> {
  return apiPost<ExperimentResultResponse>("/experiments/run", {
    experiment_config: experimentConfig,
  });
}

export function runSweep(
  sweepConfig = "behavior_sensitivity_v1",
): Promise<SweepResultResponse> {
  return apiPost<SweepResultResponse>("/experiments/sweep", {
    sweep_config: sweepConfig,
  });
}
