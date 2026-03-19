"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DelayTrendChart } from "../../../components/DelayTrendChart";
import { getDelayTrend } from "../../../lib/api";
import { TrendPoint } from "../../../lib/types";

export default function RouteDetailPage() {
  const params = useParams<{ id: string }>();
  const routeId = decodeURIComponent(params.id);

  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getDelayTrend(90, routeId, "all")
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load route analytics.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [routeId]);

  const avgDelay = data.length ? (data.reduce((sum, item) => sum + item.avg_delay, 0) / data.length).toFixed(2) : "0.00";

  return (
    <main className="page">
      <div className="header">
        <div>
          <h1>Route {routeId} Overview</h1>
          <p>90-day trend for all TTC vehicles on route {routeId}.</p>
        </div>
        <Link href="/dashboard" className="card">← Back to dashboard</Link>
      </div>

      {loading && <div className="loading">Loading route analytics…</div>}
      {error && <div className="error">{error}</div>}

      <section className="kpis">
        <div className="card"><div className="kpi-value">{data.length}</div><div className="kpi-label">Data points</div></div>
        <div className="card"><div className="kpi-value">{avgDelay}m</div><div className="kpi-label">Average delay</div></div>
      </section>

      <DelayTrendChart data={data} />
    </main>
  );
}
