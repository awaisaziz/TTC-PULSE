"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getDatasetDays, getDatasetMonths, getDatasetYears, getSummary, getTimeline } from "../lib/api";
import { SummaryPoint, TimelineGranularity, TimelinePoint, VehicleType } from "../lib/types";
import { TimelineBarChart } from "./TimelineBarChart";

type Props = {
  vehicleFilter: VehicleType;
  title: string;
  subtitle: string;
};

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function InteractiveDashboard({ vehicleFilter, title, subtitle }: Props) {
  const [years, setYears] = useState<number[]>([]);
  const [months, setMonths] = useState<number[]>([]);
  const [days, setDays] = useState<number[]>([]);
  const [summary, setSummary] = useState<SummaryPoint[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [year, setYear] = useState<number | undefined>(undefined);
  const [month, setMonth] = useState<number | undefined>(undefined);
  const [day, setDay] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getDatasetYears(vehicleFilter)
      .then((data) => {
        if (cancelled) return;
        setYears(data);
        setYear(data[data.length - 1]);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to connect to FastAPI. Check NEXT_PUBLIC_API_BASE_URL and backend service.");
      });

    return () => {
      cancelled = true;
    };
  }, [vehicleFilter]);

  useEffect(() => {
    if (!year) return;

    let cancelled = false;
    getDatasetMonths(year, vehicleFilter)
      .then((data) => {
        if (cancelled) return;
        setMonths(data);
        setMonth(undefined);
        setDay(undefined);
        setDays([]);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load available months.");
      });

    return () => {
      cancelled = true;
    };
  }, [year, vehicleFilter]);

  useEffect(() => {
    if (!year || !month) {
      setDays([]);
      setDay(undefined);
      return;
    }

    let cancelled = false;
    getDatasetDays(year, month, vehicleFilter)
      .then((data) => {
        if (cancelled) return;
        setDays(data);
        setDay(undefined);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load available days.");
      });

    return () => {
      cancelled = true;
    };
  }, [year, month, vehicleFilter]);

  useEffect(() => {
    if (!year) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const granularity: TimelineGranularity = day ? "hour" : month ? "day" : "month";

    Promise.all([getSummary(year, month, day, vehicleFilter), getTimeline(granularity, year, month, day, vehicleFilter)])
      .then(([summaryData, timelineData]) => {
        if (cancelled) return;
        setSummary(summaryData);
        setTimeline(timelineData);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Failed to connect to FastAPI. Check NEXT_PUBLIC_API_BASE_URL and backend service.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [year, month, day, vehicleFilter]);

  const summaryByVehicle = useMemo(() => {
    const map = new Map<string, SummaryPoint>();
    for (const row of summary) map.set(row.vehicle_type, row);
    return map;
  }, [summary]);

  const timelineTitle = day
    ? `Timeline by Hour (${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")})`
    : month
      ? `Timeline by Day (${year}-${String(month).padStart(2, "0")})`
      : `Timeline by Month (${year})`;

  return (
    <main className="page">
      <div className="header">
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <nav className="top-menu card">
        <Link href="/" className="menu-link">Main</Link>
        <Link href="/bus" className="menu-link">Bus</Link>
        <Link href="/subway" className="menu-link">Subway</Link>
      </nav>

      <section className="card">
        <h3>Select Year</h3>
        <div className="pill-row">
          {years.map((value) => (
            <button
              key={`year-${value}`}
              className={`pill ${year === value ? "active" : ""}`}
              onClick={() => setYear(value)}
              type="button"
            >
              {value}
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <h3>Select Month (Optional)</h3>
        <div className="pill-row">
          {months.map((value) => (
            <button
              key={`month-${value}`}
              className={`pill ${month === value ? "active" : ""}`}
              onClick={() => setMonth((current) => (current === value ? undefined : value))}
              type="button"
            >
              {MONTH_NAMES[value - 1]}
            </button>
          ))}
        </div>
      </section>

      {month && (
        <section className="card">
          <h3>Select Day (Optional)</h3>
          <div className="pill-row">
            {days.map((value) => (
              <button
                key={`day-${value}`}
                className={`pill ${day === value ? "active" : ""}`}
                onClick={() => setDay((current) => (current === value ? undefined : value))}
                type="button"
              >
                {value}
              </button>
            ))}
          </div>
        </section>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading analytics...</div>}

      <section className="kpis">
        {(vehicleFilter === "all" ? ["bus", "subway"] : [vehicleFilter]).map((type) => {
          const row = summaryByVehicle.get(type);
          return (
            <div key={type} className="card">
              <div className="kpi-label">{type.toUpperCase()}</div>
              <div className="kpi-value">{(row?.total_delay_hours ?? 0).toLocaleString()}</div>
              <div className="kpi-label">Total Hours of Delay</div>
              <div className="kpi-meta">
                {(row?.total_events ?? 0).toLocaleString()} events | Avg {(row?.avg_delay_minutes ?? 0).toFixed(2)} min
              </div>
            </div>
          );
        })}
      </section>

      <TimelineBarChart data={timeline} title={timelineTitle} />
    </main>
  );
}
