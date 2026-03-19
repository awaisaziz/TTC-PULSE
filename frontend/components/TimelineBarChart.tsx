"use client";

import { TimelinePoint } from "../lib/types";

type Props = {
  data: TimelinePoint[];
  title: string;
};

export function TimelineBarChart({ data, title }: Props) {
  const max = Math.max(1, ...data.map((point) => point.total_delay_minutes));

  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="timeline-chart">
        {data.map((point) => (
          <div key={`${point.vehicle_type}-${point.label}-${point.bucket}`} className="timeline-item">
            <div
              className={`timeline-bar ${point.vehicle_type}`}
              style={{ height: `${Math.max(8, (point.total_delay_minutes / max) * 220)}px` }}
              title={`${point.vehicle_type.toUpperCase()} - ${point.label}: ${point.total_delay_minutes.toLocaleString()} min`}
            />
            <div className="timeline-label">{point.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
