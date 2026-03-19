"use client";

import { SpatiotemporalMapPoint } from "../lib/types";

type Props = {
  data: SpatiotemporalMapPoint[];
  title: string;
};

export function SpatiotemporalMap({ data, title }: Props) {
  const width = 920;
  const height = 420;
  const pad = 20;

  if (!data.length) {
    return (
      <section className="card">
        <h3>{title}</h3>
        <div className="loading">No GTFS map points for this filter.</div>
      </section>
    );
  }

  const lats = data.map((d) => d.stop_lat);
  const lons = data.map((d) => d.stop_lon);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const maxTrips = Math.max(1, ...data.map((d) => d.trip_events));

  const toX = (lon: number) => pad + ((lon - minLon) / Math.max(1e-9, maxLon - minLon)) * (width - 2 * pad);
  const toY = (lat: number) => height - pad - ((lat - minLat) / Math.max(1e-9, maxLat - minLat)) * (height - 2 * pad);

  return (
    <section className="card">
      <h3>{title}</h3>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label="TTC GTA spatiotemporal map">
        <rect x={0} y={0} width={width} height={height} fill="#f8fafc" />
        {data.map((point) => {
          const size = 1.5 + (point.trip_events / maxTrips) * 8;
          const fill = point.vehicle_type === "bus" ? "#dc2626" : "#111827";
          return (
            <circle
              key={`${point.stop_id}-${point.hour_of_day}-${point.vehicle_type}`}
              cx={toX(point.stop_lon)}
              cy={toY(point.stop_lat)}
              r={size}
              fill={fill}
              fillOpacity={0.72}
            >
              <title>{`${point.stop_name} (${point.vehicle_type}) - ${point.trip_events.toLocaleString()} trips`}</title>
            </circle>
          );
        })}
      </svg>
      <small>Each point is a TTC GTFS stop in Toronto/GTA. Size represents scheduled trip intensity.</small>
    </section>
  );
}
