import { Panel } from "../../components/ui/Panel";
import type { MetricsSnapshot } from "../../types/simulation";

interface EpidemicHistoryChartProps {
  history: MetricsSnapshot[];
}

function pointsFor(history: MetricsSnapshot[], key: "active_infections" | "cumulative_infections"): string {
  if (history.length === 0) return "";
  const maxValue = Math.max(1, ...history.map((item) => item.cumulative_infections));
  return history
    .map((item, index) => {
      const x = history.length === 1 ? 0 : (index / (history.length - 1)) * 600;
      const y = 170 - (item[key] / maxValue) * 150;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function EpidemicHistoryChart({ history }: EpidemicHistoryChartProps) {
  const recent = history.slice(-8).reverse();

  return (
    <Panel title="Epidemic history" eyebrow="Results">
      <div className="chart-placeholder" aria-label="Epidemic history chart">
        <div className="chart-grid" />
        {history.length ? (
          <svg viewBox="0 0 600 180" role="img" aria-label="Active and cumulative infection curves">
            <polyline className="curve curve--primary" points={pointsFor(history, "active_infections")} />
            <polyline className="curve curve--secondary" points={pointsFor(history, "cumulative_infections")} />
          </svg>
        ) : (
          <span className="chart-empty">Create a simulation to begin collecting history.</span>
        )}
        <div className="chart-legend">
          <span><i className="legend-dot legend-dot--active" /> Active</span>
          <span><i className="legend-dot legend-dot--cumulative" /> Cumulative</span>
        </div>
      </div>
      {recent.length ? (
        <div className="history-table-wrap">
          <table className="history-table">
            <thead><tr><th>Tick</th><th>New</th><th>Active</th><th>Cumulative</th></tr></thead>
            <tbody>
              {recent.map((item) => (
                <tr key={item.tick}>
                  <td>{item.tick}</td>
                  <td>{item.new_infections}</td>
                  <td>{item.active_infections}</td>
                  <td>{item.cumulative_infections}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Panel>
  );
}
