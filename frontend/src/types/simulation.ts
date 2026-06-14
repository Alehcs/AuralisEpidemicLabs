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

export interface SimulationTime {
  tick: number;
  tick_minutes: number;
  day: number;
  hour: number;
  minute: number;
  time_of_day_label: string;
}

export interface ContactRecord {
  tick: number;
  zone_id: string;
  contact_count: number;
  susceptible_exposed_contacts: number;
  infectious_contacts: number;
  new_infections: number;
  average_zone_density: number;
}

export interface SimulationSnapshot {
  simulation_id: string;
  tick: number;
  day: number;
  time: SimulationTime;
  agents_summary: Record<string, number>;
  zone_summary: ZoneSummary[];
  contact_summary: ContactRecord[];
  active_policies: string[];
  metrics: MetricsSnapshot;
  sample_agents_for_visualization: Array<{
    id: string;
    zone_id: string;
    state: string;
    profile: string;
    routine_type: string;
    home_zone_id: string;
    intended_destination: string | null;
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

export interface ExportRunResponse {
  run_id: string;
  directory: string;
  files: string[];
}

export interface ExperimentRunMetric {
  final_susceptible: number;
  final_exposed: number;
  final_infected: number;
  final_recovered: number;
  cumulative_infections: number;
  peak_active_infections: number;
  tick_of_peak: number;
}

export interface VariantResult {
  variant_id: string;
  runs: Array<{
    run_id: string;
    variant_id: string;
    seed: number;
    metrics: ExperimentRunMetric;
  }>;
  aggregate: ExperimentRunMetric;
}

export interface ExperimentResultResponse {
  experiment_id: string;
  status: string;
  ticks: number;
  variants: VariantResult[];
  report: { directory: string; files: string[] };
}
