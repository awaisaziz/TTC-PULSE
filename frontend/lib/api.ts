import { HeatmapPoint, RouteSummary, TopRoute, TrendPoint, VehicleType } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    next: { revalidate: 30 },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
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
