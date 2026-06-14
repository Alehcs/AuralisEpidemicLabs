import { useState } from "react";

import { Panel } from "../../components/ui/Panel";

interface SimulationControlsProps {
  busy: boolean;
  hasSimulation: boolean;
  onCreate: () => void;
  onStep: () => void;
  onRun: (ticks: number) => void;
  onReset: () => void;
}

export function SimulationControls({
  busy,
  hasSimulation,
  onCreate,
  onStep,
  onRun,
  onReset,
}: SimulationControlsProps) {
  const [runTicks, setRunTicks] = useState(24);

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
        </div>
      </div>
      <p className="panel-note">
        {busy ? "Advancing deterministic simulation…" : "Seed 42 · 60-minute ticks · in-memory run"}
      </p>
    </Panel>
  );
}
