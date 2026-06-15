import { Panel } from "../../components/ui/Panel";
import type { SimulationSnapshot } from "../../types/simulation";
import { formatStep } from "../../utils/format";

interface MetricsPanelProps {
  snapshot: SimulationSnapshot | null;
}

export function MetricsPanel({ snapshot }: MetricsPanelProps) {
  const metrics = snapshot?.metrics;
  const time = snapshot?.time;
  const clock = time
    ? `D${time.day} ${String(time.hour).padStart(2, "0")}:${String(time.minute).padStart(2, "0")}`
    : "--";
  const values = [
    ["Simulation time", clock],
    ["Period", time?.time_of_day_label.replaceAll("_", " ") ?? "--"],
    ["Susceptible", metrics ? formatStep(metrics.susceptible_count) : "--"],
    ["Exposed", metrics ? formatStep(metrics.exposed_count) : "--"],
    ["Infected", metrics ? formatStep(metrics.infected_asymptomatic_count + metrics.infected_symptomatic_count) : "--"],
    ["Recovered", metrics ? formatStep(metrics.recovered_count) : "--"],
    ["Isolated", metrics ? formatStep(metrics.isolated_count) : "--"],
    ["Active", metrics ? formatStep(metrics.active_infections) : "--"],
    ["New this tick", metrics ? formatStep(metrics.new_infections) : "--"],
    ["Cumulative", metrics ? formatStep(metrics.cumulative_infections) : "--"],
    ["Mean risk", metrics ? `${(metrics.mean_perceived_risk * 100).toFixed(1)}%` : "--"],
    ["Alert exposure", metrics ? `${(metrics.mean_alert_exposure * 100).toFixed(1)}%` : "--"],
    ["Mean contacts", metrics ? metrics.mean_contacts.toFixed(2) : "--"],
    ["Movement reduction", metrics ? `${(metrics.movement_reduction_estimate * 100).toFixed(1)}%` : "--"],
    ["Contact reduction", metrics ? `${(metrics.contact_reduction_estimate * 100).toFixed(1)}%` : "--"],
  ];

  const pct = (value: number | undefined) =>
    value === undefined ? "--" : `${(value * 100).toFixed(1)}%`;
  const cognitive: Array<[string, string]> = [
    ["Perceived risk", pct(metrics?.mean_perceived_risk)],
    ["Real risk", pct(metrics?.mean_real_risk)],
    ["Perception gap", metrics ? `${(metrics.mean_perception_gap * 100).toFixed(1)} pp` : "--"],
    ["Trust authority", pct(metrics?.mean_trust_authority)],
    ["Trust peers", pct(metrics?.mean_trust_peers)],
    ["Fatigue", pct(metrics?.mean_fatigue)],
    ["Compliance", pct(metrics?.mean_compliance)],
    ["Fear", pct(metrics?.mean_fear)],
    ["Curiosity", pct(metrics?.mean_curiosity)],
    ["Rumor exposure", pct(metrics?.mean_rumor_exposure)],
  ];
  const information: Array<[string, string]> = [
    ["Official alert exposed", metrics ? formatStep(metrics.official_alert_exposure_count) : "--"],
    ["Rumor exposed", metrics ? formatStep(metrics.rumor_exposure_count) : "--"],
    ["False-safety exposed", metrics ? formatStep(metrics.false_safety_exposure_count) : "--"],
    ["Anti-authority exposed", metrics ? formatStep(metrics.anti_authority_exposure_count) : "--"],
    ["Peer rumor exposure", pct(metrics?.mean_peer_rumor_exposure)],
    ["Peer warning exposure", pct(metrics?.mean_peer_warning_exposure)],
  ];
  const behavior: Array<[string, string]> = [
    ["Protection behavior", pct(metrics?.mean_protection_behavior)],
    ["Distancing behavior", pct(metrics?.mean_distancing_behavior)],
    ["Risk compensation", pct(metrics?.mean_risk_compensation)],
    ["Risky movement bias", pct(metrics?.mean_risky_optional_movement_bias)],
    ["Raw contacts", metrics ? formatStep(metrics.raw_contact_count) : "--"],
    ["Effective contacts", metrics ? formatStep(metrics.effective_contact_count) : "--"],
    ["Effective β", metrics ? metrics.effective_beta_mean.toFixed(4) : "--"],
    ["Behavioral transmission ↓", pct(metrics?.behavioral_transmission_reduction)],
    ["Misinformation β ↑", metrics ? `${(metrics.misinformation_transmission_amplification * 100).toFixed(1)}%` : "--"],
  ];
  const onOff = (value: boolean | undefined) => (value ? "On" : "Off");
  const adaptive: Array<[string, string]> = [
    ["Adaptive active", metrics ? formatStep(metrics.adaptive_policy_active_count) : "--"],
    ["Trigger count", metrics ? formatStep(metrics.adaptive_policy_trigger_count) : "--"],
    ["Last rule", metrics?.last_triggered_adaptive_rule ?? "—"],
    ["Counter-messaging", onOff(metrics?.counter_messaging_active)],
    ["Peer warning campaign", onOff(metrics?.peer_warning_campaign_active)],
    ["Trust repair", onOff(metrics?.trust_repair_active)],
    ["Adaptive isolation", onOff(metrics?.adaptive_isolation_active)],
  ];

  return (
    <Panel title="Metrics" eyebrow="Live snapshot">
      <div className="metric-grid">
        {values.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="metric-group-label">Socio-cognitive state</p>
      <div className="metric-grid">
        {cognitive.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="metric-group-label">Information exposure</p>
      <div className="metric-grid">
        {information.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="metric-group-label">Behavior &amp; transmission</p>
      <div className="metric-grid">
        {behavior.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="metric-group-label">Adaptive interventions</p>
      <div className="metric-grid">
        {adaptive.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="policy-summary">
        <div>
          <span>Active policies</span>
          <strong>{snapshot?.active_policies.length ?? 0}</strong>
        </div>
        <div className="policy-list">
          {snapshot?.active_policies.length
            ? snapshot.active_policies.map((policy) => <span className="policy-chip" key={policy}>{policy}</span>)
            : <span className="policy-chip policy-chip--muted">None</span>}
        </div>
        <small>
          Local reach {metrics?.agents_under_local_alert ?? 0} · Global reach {metrics?.agents_under_global_alert ?? 0}
        </small>
      </div>
    </Panel>
  );
}
