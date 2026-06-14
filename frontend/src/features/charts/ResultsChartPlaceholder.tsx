import { Panel } from "../../components/ui/Panel";

export function ResultsChartPlaceholder() {
  return (
    <Panel title="Epidemic and cognitive curves" eyebrow="Results">
      <div className="chart-placeholder" aria-label="Future simulation result chart">
        <div className="chart-grid" />
        <svg viewBox="0 0 600 180" role="img" aria-label="Placeholder curves">
          <path className="curve curve--primary" d="M0 160 C90 158 130 110 205 74 S340 30 405 82 S520 148 600 150" />
          <path className="curve curve--secondary" d="M0 145 C110 145 160 130 220 112 S335 75 420 95 S525 123 600 108" />
        </svg>
        <span className="chart-label">Awaiting simulation data</span>
      </div>
    </Panel>
  );
}
