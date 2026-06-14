import { useCallback, useState } from "react";

import { getSimulationMetrics, createSimulation, runSimulation, stepSimulation } from "../api/simulation.api";
import { AppHeader } from "../components/layout/AppHeader";
import { EpidemicHistoryChart } from "../features/charts/EpidemicHistoryChart";
import { BackendStatusCard } from "../features/dashboard/BackendStatusCard";
import { DistrictMap } from "../features/district-map/DistrictMap";
import { MetricsPanel } from "../features/metrics-panel/MetricsPanel";
import { SimulationControls } from "../features/simulation-controls/SimulationControls";
import type { MetricsSnapshot, SimulationSnapshot, SimulationStateResponse } from "../types/simulation";

const createRequest = {
  scenario_config: "district_v1_market_outbreak",
  disease_config: "respiratory_like_v1",
  population_config: "default_population_v1",
  policy_config: "local_alert_policy",
  seed: 42,
};

export function App() {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(null);
  const [history, setHistory] = useState<MetricsSnapshot[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyResponse = useCallback(async (response: SimulationStateResponse) => {
    setSimulationId(response.simulation_id);
    setSnapshot(response.snapshot);
    const metrics = await getSimulationMetrics(response.simulation_id);
    setHistory(metrics.history);
  }, []);

  const perform = useCallback(async (operation: () => Promise<SimulationStateResponse>) => {
    setBusy(true);
    setError(null);
    try {
      await applyResponse(await operation());
    } catch (operationError) {
      setError(operationError instanceof Error ? operationError.message : "Simulation request failed");
    } finally {
      setBusy(false);
    }
  }, [applyResponse]);

  const handleCreate = () => perform(() => createSimulation(createRequest));
  const handleStep = () => simulationId && perform(() => stepSimulation(simulationId));
  const handleRun = (ticks: number) => simulationId && perform(() => runSimulation(simulationId, ticks));
  const handleReset = () => perform(() => createSimulation(createRequest));

  return (
    <div className="app-shell">
      <AppHeader />
      <BackendStatusCard />
      {error ? <div className="error-banner" role="alert">{error}</div> : null}
      <main className="dashboard-grid">
        <DistrictMap zones={snapshot?.zone_summary ?? []} />
        <div className="dashboard-sidebar">
          <SimulationControls
            busy={busy}
            hasSimulation={simulationId !== null}
            onCreate={handleCreate}
            onStep={handleStep}
            onRun={handleRun}
            onReset={handleReset}
          />
          <MetricsPanel snapshot={snapshot} />
        </div>
        <div className="results-panel">
          <EpidemicHistoryChart history={history} />
        </div>
      </main>
      <footer>Phase 1 · Deterministic SEIR agent-based simulation</footer>
    </div>
  );
}
