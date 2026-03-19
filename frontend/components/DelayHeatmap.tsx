"use client";

import { HeatmapPoint } from "../lib/types";

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

type Props = { data: HeatmapPoint[] };

function colorFor(value: number, max: number) {
  if (max === 0) return "#eef2ff";
  const intensity = value / max;
  const alpha = 0.15 + intensity * 0.85;
  return `rgba(37, 99, 235, ${alpha.toFixed(2)})`;
}

export function DelayHeatmap({ data }: Props) {
  const maxDelay = Math.max(...data.map((d) => d.avg_delay), 0);

  return (
    <div className="card">
      <h3>Delay Heatmap (Hour × Day)</h3>
      {DAYS.map((day, dayIndex) => {
        const rowData = data.filter((d) => d.day_of_week === dayIndex);

        return (
          <div key={day} className="heatmap-row">
            <div className="heatmap-label">{day}</div>
            <div className="heatmap-grid">
              {Array.from({ length: 24 }, (_, hour) => {
                const point = rowData.find((r) => r.hour_of_day === hour);
                const avg = point?.avg_delay ?? 0;
                return (
                  <div
                    key={`${day}-${hour}`}
                    className="heatmap-cell"
                    style={{ background: colorFor(avg, maxDelay) }}
                    title={`${day} ${hour}:00 — ${avg.toFixed(1)} min avg delay`}
                  />
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
