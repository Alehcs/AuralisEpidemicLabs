import { Panel } from "../../components/ui/Panel";

const metrics = [
  ["Population", "5,000"],
  ["Simulation step", "0"],
  ["Active cases", "--"],
  ["Perceived risk", "--"],
];

export function MetricsPanelPlaceholder() {
  return (
    <Panel title="Metrics" eyebrow="Live snapshot">
      <div className="metric-grid">
        {metrics.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </Panel>
  );
}
