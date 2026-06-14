import { Panel } from "../../components/ui/Panel";

export function SimulationControlsPlaceholder() {
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
        <div className="button-row">
          <button type="button" disabled>Start</button>
          <button type="button" className="button-secondary" disabled>Step</button>
        </div>
      </div>
      <p className="panel-note">Controls are intentionally inactive during technical setup.</p>
    </Panel>
  );
}
