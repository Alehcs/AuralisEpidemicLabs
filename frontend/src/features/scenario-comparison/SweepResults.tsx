import { Panel } from "../../components/ui/Panel";
import type { SweepResultResponse } from "../../types/simulation";

interface SweepResultsProps {
  result: SweepResultResponse | null;
}

const fmt = (value: number | undefined, digits = 2) =>
  value === undefined ? "--" : value.toFixed(digits);

const pct = (value: number | undefined) =>
  value === undefined ? "--" : `${(value * 100).toFixed(1)}%`;

export function SweepResults({ result }: SweepResultsProps) {
  if (!result) return null;

  const paramNames = Object.keys(result.parameter_grid);
  const best = result.best_response;

  return (
    <Panel title="Sensitivity sweep" eyebrow="Calibration">
      <p className="panel-note">
        Focus variant <strong>{result.focus_variant}</strong> · best response at point #{best.point_index}{" "}
        ({paramNames.map((name) => `${name}=${best.parameters[name]}`).join(", ")}) with cumulative{" "}
        {fmt(best.focus_metrics.cumulative_infections, 0)}.
      </p>
      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              {paramNames.map((name) => (
                <th key={name}>{name.replaceAll("_", " ")}</th>
              ))}
              <th>Cumulative</th>
              <th>Peak active</th>
              <th>Eff β</th>
              <th>Protection</th>
              <th>Risk comp</th>
              <th>Misinfo β ↑</th>
              <th>Behav ↓</th>
              <th>Adapt. triggers</th>
            </tr>
          </thead>
          <tbody>
            {result.points.map((point) => (
              <tr key={point.point_index}>
                <td>{point.point_index}</td>
                {paramNames.map((name) => (
                  <td key={name}>{point.parameters[name]}</td>
                ))}
                <td>{fmt(point.focus_metrics.cumulative_infections, 0)}</td>
                <td>{fmt(point.focus_metrics.peak_active_infections, 0)}</td>
                <td>{fmt(point.focus_metrics.effective_beta_mean, 4)}</td>
                <td>{pct(point.focus_metrics.mean_protection_behavior)}</td>
                <td>{pct(point.focus_metrics.mean_risk_compensation)}</td>
                <td>{pct(point.focus_metrics.misinformation_transmission_amplification)}</td>
                <td>{pct(point.focus_metrics.behavioral_transmission_reduction)}</td>
                <td>{fmt(point.focus_metrics.adaptive_policy_trigger_count, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="panel-note">
        Each row reruns experiment <strong>{result.experiment_config}</strong> with the listed behavior-strength
        overrides, holding seeds and structure fixed.
      </p>
    </Panel>
  );
}
