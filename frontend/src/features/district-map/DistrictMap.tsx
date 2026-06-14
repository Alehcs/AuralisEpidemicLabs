import { Panel } from "../../components/ui/Panel";
import type { ContactRecord, ZoneSummary } from "../../types/simulation";

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
  contacts: ContactRecord[];
}

function riskBand(risk: number): string {
  if (risk >= 0.1) return "high";
  if (risk >= 0.03) return "medium";
  return "low";
}

export function DistrictMap({ zones, contacts }: DistrictMapProps) {
  const contactsByZone = new Map(contacts.map((record) => [record.zone_id, record]));
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
        mean_perceived_risk: 0,
        mean_alert_exposure: 0,
        mean_rumor_exposure: 0,
        mean_fatigue: 0,
        active_policies: [],
      }));

  return (
    <Panel title="District zones" eyebrow="Spatial layer" className="map-panel">
      <div className="zone-grid">
        {displayedZones.map((zone) => (
          <article
            className={`zone-card zone-card--${riskBand(zone.risk_level_simple)} ${zone.active_policies.length ? "zone-card--policy" : ""}`}
            key={zone.zone_id}
          >
            <div className="zone-card__heading">
              <strong>{zoneNames[zone.zone_id] ?? zone.zone_id}</strong>
              <span>{(zone.risk_level_simple * 100).toFixed(1)}% risk</span>
            </div>
            {zone.active_policies.length ? (
              <div className="zone-policy-row">
                {zone.active_policies.map((policy) => (
                  <span className={policy.includes("closure") ? "zone-policy zone-policy--closure" : "zone-policy"} key={policy}>
                    {policy.includes("closure") ? "Closure" : "Local policy"}
                  </span>
                ))}
              </div>
            ) : null}
            <div className="zone-card__metrics">
              <span>Population <b>{zone.population}</b></span>
              <span>Exposed <b>{zone.exposed}</b></span>
              <span>Infected <b>{zone.infected}</b></span>
              <span>Recovered <b>{zone.recovered}</b></span>
              <span>Contacts <b>{contactsByZone.get(zone.zone_id)?.contact_count ?? 0}</b></span>
              <span>New cases <b>{contactsByZone.get(zone.zone_id)?.new_infections ?? 0}</b></span>
              <span>Perceived risk <b>{(zone.mean_perceived_risk * 100).toFixed(1)}%</b></span>
              <span>Alert exposure <b>{(zone.mean_alert_exposure * 100).toFixed(1)}%</b></span>
              <span>Rumor exposure <b>{(zone.mean_rumor_exposure * 100).toFixed(1)}%</b></span>
              <span>Fatigue <b>{(zone.mean_fatigue * 100).toFixed(1)}%</b></span>
            </div>
          </article>
        ))}
      </div>
      <p className="panel-note">Epidemic risk, perceived risk, and policy reach are reported independently per zone.</p>
    </Panel>
  );
}
