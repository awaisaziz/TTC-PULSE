"use client";

import Link from "next/link";
import { TopRoute } from "../lib/types";

type Props = { data: TopRoute[] };

export function RouteRankingChart({ data }: Props) {
  const maxDelay = Math.max(1, ...data.map((d) => d.avg_delay));

  return (
    <div className="card">
      <h3>Route Ranking (Average Delay)</h3>
      <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
        {data.map((route) => {
          const width = `${(route.avg_delay / maxDelay) * 100}%`;
          return (
            <div key={`${route.route_id}-${route.vehicle_type}`}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                <span>{route.route_id}</span>
                <span>{route.avg_delay}m</span>
              </div>
              <div style={{ background: "#e5e7eb", borderRadius: 999, height: 10 }}>
                <div style={{ width, background: "#2563eb", borderRadius: 999, height: "100%" }} />
              </div>
            </div>
          );
        })}
      </div>
      <table className="table">
        <thead>
          <tr><th>Route</th><th>Vehicle</th><th>Avg</th><th>Events</th></tr>
        </thead>
        <tbody>
          {data.map((route) => (
            <tr key={`${route.route_id}-${route.vehicle_type}`}>
              <td><Link href={`/route/${route.route_id}`}>{route.route_id}</Link></td>
              <td>{route.vehicle_type}</td>
              <td>{route.avg_delay}m</td>
              <td>{route.event_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
