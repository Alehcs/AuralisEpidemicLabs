import { useState } from "react";

import { Panel } from "../../components/ui/Panel";

const EXPERIMENTS = [
  { id: "global_vs_local_alert", label: "Baseline vs alerts" },
  { id: "official_alert_vs_rumors", label: "Official vs rumors" },
  { id: "misinformation_epidemic_impact", label: "Misinformation impact" },
  { id: "adaptive_counter_misinformation", label: "Adaptive counter-misinformation" },
  { id: "static_vs_adaptive_policy", label: "Static vs adaptive policy" },
];

interface SimulationControlsProps {
  busy: boolean;
  hasSimulation: boolean;
  onCreate: () => void;
  onStep: () => void;
  onRun: (ticks: number) => void;
  onReset: () => void;
  onExport: () => void;
  onRunExperiment: (experimentConfig: string) => void;
  onRunSweep: () => void;
}

export function SimulationControls({
  busy,
  hasSimulation,
  onCreate,
  onStep,
  onRun,
  onReset,
  onExport,
  onRunExperiment,
  onRunSweep,
}: SimulationControlsProps) {
  const [runTicks, setRunTicks] = useState(24);
  const [experiment, setExperiment] = useState("global_vs_local_alert");

  return (
    <Panel title="Simulation controls" eyebrow="Interactive run">
      <div className="control-stack">
        <label>
          Scenario
          <select defaultValue="district" disabled>
            <option value="district">District V1 - Market Outbreak</option>
          </select>
        </label>
        <label>
          Disease
          <select defaultValue="respiratory" disabled>
            <option value="respiratory">Respiratory-like V1</option>
          </select>
        </label>
        <label>
          Run ticks
          <input
            type="number"
            min="1"
            max="10000"
            value={runTicks}
            onChange={(event) => setRunTicks(Number(event.target.value))}
          />
        </label>
        <label>
          Experiment
          <select value={experiment} onChange={(event) => setExperiment(event.target.value)}>
            {EXPERIMENTS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <div className="button-grid">
          <button type="button" disabled={busy || hasSimulation} onClick={onCreate}>
            Create simulation
          </button>
          <button type="button" className="button-secondary" disabled={busy || !hasSimulation} onClick={onStep}>
            Step
          </button>
          <button
            type="button"
            className="button-secondary"
            disabled={busy || !hasSimulation || runTicks < 1}
            onClick={() => onRun(runTicks)}
          >
            Run {runTicks} ticks
          </button>
          <button type="button" className="button-danger" disabled={busy || !hasSimulation} onClick={onReset}>
            Reset
          </button>
          <button type="button" className="button-secondary" disabled={busy || !hasSimulation} onClick={onExport}>
            Export current run
          </button>
          <button type="button" className="button-secondary" disabled={busy} onClick={() => onRunExperiment(experiment)}>
            Run experiment
          </button>
          <button type="button" className="button-secondary" disabled={busy} onClick={onRunSweep}>
            Run sensitivity sweep
          </button>
        </div>
      </div>
      <p className="panel-note">
        {busy
          ? "Running deterministic operation…"
          : "Seed 42 · cognition, behavior, rumors & adaptive interventions"}
      </p>
    </Panel>
  );
}
