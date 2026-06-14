import { Panel } from "../../components/ui/Panel";
import type { ZoneSummary } from "../../types/simulation";

const zoneNames: Record<string, string> = {
  residential_north: "Residential North",
  residential_south: "Residential South",
  market: "Market",
  transport: "Transport",
  work_school: "Work / School",
  hospital: "Hospital",
  plaza: "Plaza",
  periphery: "Periphery",
};

interface DistrictMapProps {
  zones: ZoneSummary[];
}

function riskBand(risk: number): string {
  if (risk >= 0.1) return "high";
  if (risk >= 0.03) return "medium";
  return "low";
}

export function DistrictMap({ zones }: DistrictMapProps) {
  const displayedZones = zones.length
    ? zones
    : Object.keys(zoneNames).map((zone_id) => ({
        zone_id,
        population: 0,
        susceptible: 0,
        exposed: 0,
        infected: 0,
        recovered: 0,
        risk_level_simple: 0,
      }));

  return (
    <Panel title="District zones" eyebrow="Spatial layer" className="map-panel">
      <div className="zone-grid">
        {displayedZones.map((zone) => (
          <article className={`zone-card zone-card--${riskBand(zone.risk_level_simple)}`} key={zone.zone_id}>
            <div className="zone-card__heading">
              <strong>{zoneNames[zone.zone_id] ?? zone.zone_id}</strong>
              <span>{(zone.risk_level_simple * 100).toFixed(1)}% risk</span>
            </div>
            <div className="zone-card__metrics">
              <span>Population <b>{zone.population}</b></span>
              <span>Exposed <b>{zone.exposed}</b></span>
              <span>Infected <b>{zone.infected}</b></span>
              <span>Recovered <b>{zone.recovered}</b></span>
            </div>
          </article>
        ))}
      </div>
      <p className="panel-note">Risk is the local exposed plus infected ratio. Geometry remains a later-phase concern.</p>
    </Panel>
  );
}
