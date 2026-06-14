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
  active_policy_count: number;
  agents_under_local_alert: number;
  agents_under_global_alert: number;
  mean_perceived_risk: number;
  mean_alert_exposure: number;
  mean_contacts: number;
  movement_reduction_estimate: number;
  contact_reduction_estimate: number;
  mean_real_risk: number;
  mean_perception_gap: number;
  mean_trust_authority: number;
  mean_trust_peers: number;
  mean_fatigue: number;
  mean_fear: number;
  mean_curiosity: number;
  mean_compliance: number;
  mean_rumor_belief: number;
  mean_rumor_exposure: number;
  rumor_exposure_count: number;
  official_alert_exposure_count: number;
  false_safety_exposure_count: number;
  anti_authority_exposure_count: number;
  mean_protection_behavior: number;
  mean_distancing_behavior: number;
  mean_risk_compensation: number;
  mean_risky_optional_movement_bias: number;
  mean_peer_rumor_exposure: number;
  mean_peer_warning_exposure: number;
  raw_contact_count: number;
  effective_contact_count: number;
  effective_beta_mean: number;
  behavioral_transmission_reduction: number;
  misinformation_transmission_amplification: number;
  rumor_pressure: number;
  peer_warning_pressure: number;
  policy_effect_summary: Record<string, unknown>;
}

export interface ZoneSummary {
  zone_id: string;
  population: number;
  susceptible: number;
  exposed: number;
  infected: number;
  recovered: number;
  risk_level_simple: number;
  mean_perceived_risk: number;
  mean_alert_exposure: number;
  mean_rumor_exposure: number;
  mean_fatigue: number;
  active_policies: string[];
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
  sample_agents_for_visualization: SampleAgent[];
}

export interface SampleAgent {
  id: string;
  zone_id: string;
  state: string;
  profile: string;
  routine_type: string;
  home_zone_id: string;
  intended_destination: string | null;
  perceived_risk: number;
  real_risk: number;
  alert_exposure: number;
  rumor_exposure: number;
  compliance_tendency: number;
  adaptive_compliance: number;
  trust_authority: number;
  fatigue: number;
  protection_behavior: number;
  distancing_behavior: number;
  risk_compensation: number;
  peer_rumor_exposure: number;
  peer_warning_exposure: number;
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
  policy_config: string | null;
  policy_configs: string[];
  information_configs: string[];
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
  mean_perceived_risk: number;
  mean_alert_exposure: number;
  mean_contacts: number;
  mean_movement_reduction: number;
  mean_contact_reduction: number;
  mean_real_risk: number;
  mean_perception_gap: number;
  mean_trust_authority: number;
  mean_fatigue: number;
  mean_compliance: number;
  mean_rumor_exposure: number;
  mean_protection_behavior: number;
  mean_distancing_behavior: number;
  mean_risk_compensation: number;
  effective_contact_count: number;
  effective_beta_mean: number;
  behavioral_transmission_reduction: number;
  misinformation_transmission_amplification: number;
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
