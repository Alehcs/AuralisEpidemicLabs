import { Panel } from "../../components/ui/Panel";

const zones = [
  "Residential North",
  "Market",
  "Transport",
  "Work / School",
  "Hospital",
  "Plaza",
];

export function DistrictMapPlaceholder() {
  return (
    <Panel title="District map" eyebrow="Spatial layer" className="map-panel">
      <div className="map-placeholder">
        {zones.map((zone, index) => (
          <div className={`map-zone map-zone--${index + 1}`} key={zone}>
            <span>{zone}</span>
          </div>
        ))}
        <div className="map-route map-route--one" />
        <div className="map-route map-route--two" />
      </div>
      <p className="panel-note">Zone geometry, routes, and agent movement arrive in later phases.</p>
    </Panel>
  );
}
