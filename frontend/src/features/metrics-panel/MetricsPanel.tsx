import { Panel } from "../../components/ui/Panel";
import type { SimulationSnapshot } from "../../types/simulation";
import { formatStep } from "../../utils/format";

interface MetricsPanelProps {
  snapshot: SimulationSnapshot | null;
}

export function MetricsPanel({ snapshot }: MetricsPanelProps) {
  const metrics = snapshot?.metrics;
  const values = [
    ["Tick / day", snapshot ? `${snapshot.tick} / ${snapshot.day.toFixed(2)}` : "--"],
    ["Susceptible", metrics ? formatStep(metrics.susceptible_count) : "--"],
    ["Exposed", metrics ? formatStep(metrics.exposed_count) : "--"],
    ["Infected", metrics ? formatStep(metrics.infected_asymptomatic_count + metrics.infected_symptomatic_count) : "--"],
    ["Recovered", metrics ? formatStep(metrics.recovered_count) : "--"],
    ["Active", metrics ? formatStep(metrics.active_infections) : "--"],
    ["New this tick", metrics ? formatStep(metrics.new_infections) : "--"],
    ["Cumulative", metrics ? formatStep(metrics.cumulative_infections) : "--"],
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
    </Panel>
  );
}
