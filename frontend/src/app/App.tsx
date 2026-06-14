import { useCallback, useState } from "react";

import {
  createSimulation,
  exportSimulation,
  getSimulationMetrics,
  runBatchExperiment,
  runSimulation,
  stepSimulation,
} from "../api/simulation.api";
import { AppHeader } from "../components/layout/AppHeader";
import { EpidemicHistoryChart } from "../features/charts/EpidemicHistoryChart";
import { BackendStatusCard } from "../features/dashboard/BackendStatusCard";
import { DistrictMap } from "../features/district-map/DistrictMap";
import { MetricsPanel } from "../features/metrics-panel/MetricsPanel";
import { ExperimentResults } from "../features/scenario-comparison/ExperimentResults";
import { SimulationControls } from "../features/simulation-controls/SimulationControls";
import type {
  ExperimentResultResponse,
  MetricsSnapshot,
  SimulationSnapshot,
  SimulationStateResponse,
} from "../types/simulation";

const createRequest = {
  scenario_config: "district_v1_market_outbreak",
  disease_config: "respiratory_like_v1",
  population_config: "default_population_v1",
  policy_config: null,
  policy_configs: ["local_alert_policy", "isolation_encouragement_policy"],
  information_configs: ["false_safety_market"],
  seed: 42,
};

export function App() {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(null);
  const [history, setHistory] = useState<MetricsSnapshot[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [experimentResult, setExperimentResult] = useState<ExperimentResultResponse | null>(null);

  const applyResponse = useCallback(async (response: SimulationStateResponse) => {
    setSimulationId(response.simulation_id);
    setSnapshot(response.snapshot);
    const metrics = await getSimulationMetrics(response.simulation_id);
    setHistory(metrics.history);
  }, []);

  const perform = useCallback(async (operation: () => Promise<SimulationStateResponse>) => {
    setBusy(true);
    setError(null);
    setNotice(null);
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
  const handleExport = async () => {
    if (!simulationId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await exportSimulation(simulationId);
      setNotice(`Exported ${result.files.length} files for run ${result.run_id}.`);
    } catch (operationError) {
      setError(operationError instanceof Error ? operationError.message : "Export failed");
    } finally {
      setBusy(false);
    }
  };
  const runExperiment = useCallback(async (experimentConfig: string) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await runBatchExperiment(experimentConfig);
      setExperimentResult(result);
      setNotice(`Batch experiment ${result.experiment_id} completed.`);
    } catch (operationError) {
      setError(operationError instanceof Error ? operationError.message : "Experiment failed");
    } finally {
      setBusy(false);
    }
  }, []);
  const handleRunExperiment = () => runExperiment("global_vs_local_alert");
  const handleRunRumorExperiment = () => runExperiment("official_alert_vs_rumors");
  const handleRunMisinformationExperiment = () => runExperiment("misinformation_epidemic_impact");

  return (
    <div className="app-shell">
      <AppHeader />
      <BackendStatusCard />
      {error ? <div className="error-banner" role="alert">{error}</div> : null}
      {notice ? <div className="notice-banner" role="status">{notice}</div> : null}
      <main className="dashboard-grid">
        <DistrictMap
          zones={snapshot?.zone_summary ?? []}
          contacts={snapshot?.contact_summary ?? []}
        />
        <div className="dashboard-sidebar">
          <SimulationControls
            busy={busy}
            hasSimulation={simulationId !== null}
            onCreate={handleCreate}
            onStep={handleStep}
            onRun={handleRun}
            onReset={handleReset}
            onExport={handleExport}
            onRunExperiment={handleRunExperiment}
            onRunRumorExperiment={handleRunRumorExperiment}
            onRunMisinformationExperiment={handleRunMisinformationExperiment}
          />
          <MetricsPanel snapshot={snapshot} />
        </div>
        <div className="results-panel">
          <EpidemicHistoryChart history={history} />
        </div>
        <div className="results-panel">
          <ExperimentResults result={experimentResult} />
        </div>
      </main>
      <footer>Phase 5 · Behavior-driven transmission feedback and light social rumor propagation</footer>
    </div>
  );
}
