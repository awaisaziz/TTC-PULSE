import {
  HeatmapPoint,
  RouteSummary,
  SummaryPoint,
  TimelineGranularity,
  TimelinePoint,
  TopRoute,
  TrendPoint,
  VehicleType,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchApi<T>(path: string): Promise<T> {
  const candidates = [API_BASE, "http://localhost:8000", "http://127.0.0.1:8000"];
  const uniqueCandidates = Array.from(new Set(candidates));
  let lastError: Error | null = null;

  for (const base of uniqueCandidates) {
    try {
      const response = await fetch(`${base}${path}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      lastError = error as Error;
    }
  }

  throw lastError ?? new Error("API request failed");
}

export async function getRoutes(): Promise<RouteSummary[]> {
  const payload = await fetchApi<{ data: RouteSummary[] }>("/routes");
  return payload.data;
}

export async function getDelayTrend(days: number, routeId?: string, vehicleType: VehicleType = "all"): Promise<TrendPoint[]> {
  const params = new URLSearchParams({ days: String(days) });
  if (routeId && routeId !== "all") params.set("route_id", routeId);
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);

  const payload = await fetchApi<{ data: TrendPoint[] }>(`/delay-trend?${params.toString()}`);
  return payload.data;
}

export async function getTopRoutes(days: number, vehicleType: VehicleType = "all", minEvents = 60): Promise<TopRoute[]> {
  const params = new URLSearchParams({ limit: "10", min_events: String(minEvents), days: String(days) });
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);

  const payload = await fetchApi<{ data: TopRoute[] }>(`/top-routes?${params.toString()}`);
  return payload.data;
}

export async function getHeatmap(days: number, vehicleType: VehicleType = "all"): Promise<HeatmapPoint[]> {
  const params = new URLSearchParams({ days: String(days) });
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);

  const payload = await fetchApi<{ data: HeatmapPoint[] }>(`/heatmap?${params.toString()}`);
  return payload.data;
}

export async function getDatasetYears(vehicleType: VehicleType = "all"): Promise<number[]> {
  const params = new URLSearchParams();
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);
  const payload = await fetchApi<{ data: number[] }>(`/dataset-years?${params.toString()}`);
  return payload.data;
}

export async function getDatasetMonths(year: number, vehicleType: VehicleType = "all"): Promise<number[]> {
  const params = new URLSearchParams({ year: String(year) });
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);
  const payload = await fetchApi<{ data: number[] }>(`/dataset-months?${params.toString()}`);
  return payload.data;
}

export async function getDatasetDays(year: number, month: number, vehicleType: VehicleType = "all"): Promise<number[]> {
  const params = new URLSearchParams({ year: String(year), month: String(month) });
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);
  const payload = await fetchApi<{ data: number[] }>(`/dataset-days?${params.toString()}`);
  return payload.data;
}

export async function getSummary(
  year?: number,
  month?: number,
  day?: number,
  vehicleType: VehicleType = "all",
): Promise<SummaryPoint[]> {
  const params = new URLSearchParams();
  if (year) params.set("year", String(year));
  if (month) params.set("month", String(month));
  if (day) params.set("day", String(day));
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);
  const payload = await fetchApi<{ data: SummaryPoint[] }>(`/summary?${params.toString()}`);
  return payload.data;
}

export async function getTimeline(
  granularity: TimelineGranularity,
  year?: number,
  month?: number,
  day?: number,
  vehicleType: VehicleType = "all",
): Promise<TimelinePoint[]> {
  const params = new URLSearchParams({ granularity });
  if (year) params.set("year", String(year));
  if (month) params.set("month", String(month));
  if (day) params.set("day", String(day));
  if (vehicleType !== "all") params.set("vehicle_type", vehicleType);
  const payload = await fetchApi<{ data: TimelinePoint[] }>(`/timeline?${params.toString()}`);
  return payload.data;
}
