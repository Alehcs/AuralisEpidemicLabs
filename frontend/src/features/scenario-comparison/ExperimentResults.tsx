import { Panel } from "../../components/ui/Panel";
import type { ExperimentResultResponse } from "../../types/simulation";

interface ExperimentResultsProps {
  result: ExperimentResultResponse | null;
}

export function ExperimentResults({ result }: ExperimentResultsProps) {
  if (!result) return null;

  return (
    <Panel title="Batch experiment" eyebrow="Scenario comparison">
      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>Variant</th>
              <th>Final S</th>
              <th>Final I</th>
              <th>Cumulative</th>
              <th>Peak active</th>
              <th>Peak tick</th>
              <th>Perceived</th>
              <th>Real risk</th>
              <th>Gap (pp)</th>
              <th>Trust auth</th>
              <th>Fatigue</th>
              <th>Protection</th>
              <th>Eff contacts</th>
              <th>Eff β</th>
              <th>Behav ↓</th>
              <th>Misinfo β ↑</th>
              <th>Adapt. triggers</th>
            </tr>
          </thead>
          <tbody>
            {result.variants.map((variant) => (
              <tr key={variant.variant_id}>
                <td>{variant.variant_id}</td>
                <td>{variant.aggregate.final_susceptible.toFixed(0)}</td>
                <td>{variant.aggregate.final_infected.toFixed(0)}</td>
                <td>{variant.aggregate.cumulative_infections.toFixed(0)}</td>
                <td>{variant.aggregate.peak_active_infections.toFixed(0)}</td>
                <td>{variant.aggregate.tick_of_peak.toFixed(1)}</td>
                <td>{(variant.aggregate.mean_perceived_risk * 100).toFixed(1)}%</td>
                <td>{(variant.aggregate.mean_real_risk * 100).toFixed(1)}%</td>
                <td>{(variant.aggregate.mean_perception_gap * 100).toFixed(1)}</td>
                <td>{(variant.aggregate.mean_trust_authority * 100).toFixed(1)}%</td>
                <td>{(variant.aggregate.mean_fatigue * 100).toFixed(1)}%</td>
                <td>{(variant.aggregate.mean_protection_behavior * 100).toFixed(1)}%</td>
                <td>{variant.aggregate.effective_contact_count.toFixed(0)}</td>
                <td>{variant.aggregate.effective_beta_mean.toFixed(4)}</td>
                <td>{(variant.aggregate.behavioral_transmission_reduction * 100).toFixed(1)}%</td>
                <td>{(variant.aggregate.misinformation_transmission_amplification * 100).toFixed(1)}%</td>
                <td>{variant.aggregate.adaptive_policy_trigger_count.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="panel-note">
        Variants share seeds and differ only by their official-policy and information event set, exposing how
        rumors and distrust shift perceived risk, trust and fatigue independently of real risk.
      </p>
    </Panel>
  );
}
