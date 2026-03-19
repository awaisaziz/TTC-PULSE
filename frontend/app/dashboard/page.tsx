"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { DelayHeatmap } from "../../components/DelayHeatmap";
import { DelayTrendChart } from "../../components/DelayTrendChart";
import { Filters } from "../../components/Filters";
import { RouteRankingChart } from "../../components/RouteRankingChart";
import { getDelayTrend, getHeatmap, getRoutes, getTopRoutes } from "../../lib/api";
import { HeatmapPoint, RouteSummary, TopRoute, TrendPoint, VehicleType } from "../../lib/types";

const cache = new Map<string, unknown>();

export default function DashboardPage() {
  const [route, setRoute] = useState("all");
  const [timeWindow, setTimeWindow] = useState(30);
  const [vehicleType, setVehicleType] = useState<VehicleType>("all");

  const [routes, setRoutes] = useState<RouteSummary[]>([]);
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [rankingData, setRankingData] = useState<TopRoute[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const routeKey = "routes";
        const trendKey = `trend-${timeWindow}-${route}-${vehicleType}`;
        const rankingKey = `ranking-${timeWindow}-${vehicleType}`;
        const heatmapKey = `heatmap-${timeWindow}-${vehicleType}`;

        const [routeRes, trendRes, rankingRes, heatmapRes] = await Promise.all([
          cache.has(routeKey) ? Promise.resolve(cache.get(routeKey) as RouteSummary[]) : getRoutes(),
          cache.has(trendKey) ? Promise.resolve(cache.get(trendKey) as TrendPoint[]) : getDelayTrend(timeWindow, route, vehicleType),
          cache.has(rankingKey) ? Promise.resolve(cache.get(rankingKey) as TopRoute[]) : getTopRoutes(timeWindow, vehicleType),
          cache.has(heatmapKey) ? Promise.resolve(cache.get(heatmapKey) as HeatmapPoint[]) : getHeatmap(timeWindow, vehicleType),
        ]);

        cache.set(routeKey, routeRes);
        cache.set(trendKey, trendRes);
        cache.set(rankingKey, rankingRes);
        cache.set(heatmapKey, heatmapRes);

        if (!cancelled) {
          setRoutes(routeRes);
          setTrendData(trendRes);
          setRankingData(rankingRes);
          setHeatmapData(heatmapRes);
        }
      } catch {
        if (!cancelled) setError("Failed to connect to FastAPI. Check NEXT_PUBLIC_API_BASE_URL and backend service.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [route, timeWindow, vehicleType]);

  const totalEvents = useMemo(() => trendData.reduce((acc, point) => acc + point.event_count, 0), [trendData]);

  if (error) return <div className="error">{error}</div>;

  return (
    <main className="page">
      <div className="header">
        <div>
          <h1>TTC Analytics Dashboard</h1>
          <p>Interactive delay analytics with live data from FastAPI.</p>
        </div>
        {route !== "all" && <Link className="card" href={`/route/${route}`}>Open route detail →</Link>}
      </div>

      <Filters
        routes={routes.map((r) => r.route_id)}
        selectedRoute={route}
        onRouteChange={setRoute}
        timeWindow={timeWindow}
        onTimeWindowChange={setTimeWindow}
        vehicleType={vehicleType}
        onVehicleTypeChange={setVehicleType}
      />

      <section className="kpis">
        <div className="card"><div className="kpi-value">{trendData.length}</div><div className="kpi-label">Trend points</div></div>
        <div className="card"><div className="kpi-value">{rankingData.length}</div><div className="kpi-label">Ranked routes</div></div>
        <div className="card"><div className="kpi-value">{totalEvents.toLocaleString()}</div><div className="kpi-label">Events in range</div></div>
      </section>

      {loading && <div className="loading">Loading dashboard data…</div>}

      <section className="grid grid-2">
        <DelayTrendChart data={trendData} />
        <RouteRankingChart data={rankingData} />
      </section>
      <section style={{ marginTop: 16 }}>
        <DelayHeatmap data={heatmapData} />
      </section>
    </main>
  );
}
