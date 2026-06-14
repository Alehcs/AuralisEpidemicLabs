import { AppHeader } from "../components/layout/AppHeader";
import { ResultsChartPlaceholder } from "../features/charts/ResultsChartPlaceholder";
import { BackendStatusCard } from "../features/dashboard/BackendStatusCard";
import { DistrictMapPlaceholder } from "../features/district-map/DistrictMapPlaceholder";
import { MetricsPanelPlaceholder } from "../features/metrics-panel/MetricsPanelPlaceholder";
import { SimulationControlsPlaceholder } from "../features/simulation-controls/SimulationControlsPlaceholder";

export function App() {
  return (
    <div className="app-shell">
      <AppHeader />
      <BackendStatusCard />
      <main className="dashboard-grid">
        <DistrictMapPlaceholder />
        <div className="dashboard-sidebar">
          <SimulationControlsPlaceholder />
          <MetricsPanelPlaceholder />
        </div>
        <div className="results-panel">
          <ResultsChartPlaceholder />
        </div>
      </main>
      <footer>Technical foundation · Interactive and headless simulation ready</footer>
    </div>
  );
}
