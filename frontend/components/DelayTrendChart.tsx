"use client";

import { TrendPoint } from "../lib/types";

type Props = { data: TrendPoint[] };

export function DelayTrendChart({ data }: Props) {
  const width = 760;
  const height = 260;
  const pad = 28;

  const maxY = Math.max(1, ...data.map((d) => Math.max(d.avg_delay, d.p90_delay)));
  const toX = (idx: number) => pad + (idx / Math.max(1, data.length - 1)) * (width - pad * 2);
  const toY = (value: number) => height - pad - (value / maxY) * (height - pad * 2);

  const avgPath = data
    .map((d, i) => `${i === 0 ? "M" : "L"}${toX(i)},${toY(d.avg_delay)}`)
    .join(" ");
  const p90Path = data
    .map((d, i) => `${i === 0 ? "M" : "L"}${toX(i)},${toY(d.p90_delay)}`)
    .join(" ");

  return (
    <div className="card">
      <h3>Delay Trends</h3>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label="Delay trend chart">
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#9ca3af" />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="#9ca3af" />
        {avgPath && <path d={avgPath} fill="none" stroke="#2563eb" strokeWidth="2" />}
        {p90Path && <path d={p90Path} fill="none" stroke="#ef4444" strokeWidth="2" />}
      </svg>
      <small>Blue: Avg delay, Red: P90 delay</small>
    </div>
  );
}
