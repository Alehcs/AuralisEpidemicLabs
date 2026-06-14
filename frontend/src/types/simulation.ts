export interface MetricsSnapshot {
  tick: number;
  susceptible_count: number;
  exposed_count: number;
  infected_asymptomatic_count: number;
  infected_symptomatic_count: number;
  recovered_count: number;
  isolated_count: number;
  new_infections: number;
  active_infections: number;
  cumulative_infections: number;
}

export interface ZoneSummary {
  zone_id: string;
  population: number;
  susceptible: number;
  exposed: number;
  infected: number;
  recovered: number;
  risk_level_simple: number;
}

export interface SimulationSnapshot {
  simulation_id: string;
  tick: number;
  day: number;
  agents_summary: Record<string, number>;
  zone_summary: ZoneSummary[];
  metrics: MetricsSnapshot;
  sample_agents_for_visualization: Array<{
    id: string;
    zone_id: string;
    state: string;
    profile: string;
  }>;
}

export interface SimulationStateResponse {
  simulation_id: string;
  status: string;
  current_step: number;
  message: string;
  snapshot: SimulationSnapshot;
}

export interface SimulationMetricsResponse {
  simulation_id: string;
  history: MetricsSnapshot[];
}

export interface SimulationCreateRequest {
  scenario_config: string;
  disease_config: string;
  population_config: string;
  policy_config: string;
  seed: number;
}
