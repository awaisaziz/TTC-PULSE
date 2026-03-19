export type VehicleType = "all" | "bus" | "subway";

export type RouteSummary = {
  route_id: string;
  vehicle_type: "bus" | "subway";
  event_count: number;
  avg_delay: number;
};

export type TrendPoint = {
  service_date: string;
  route_id: string;
  vehicle_type: "bus" | "subway";
  event_count: number;
  avg_delay: number;
  p90_delay: number;
};

export type TopRoute = {
  route_id: string;
  vehicle_type: "bus" | "subway";
  event_count: number;
  avg_delay: number;
  p90_delay: number;
};

export type HeatmapPoint = {
  day_of_week: number;
  hour_of_day: number;
  vehicle_type: "bus" | "subway";
  event_count: number;
  avg_delay: number;
};
