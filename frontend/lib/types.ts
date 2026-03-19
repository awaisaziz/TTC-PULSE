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

export type TimelineGranularity = "month" | "day" | "hour";

export type SummaryPoint = {
  vehicle_type: "bus" | "subway";
  total_events: number;
  total_delay_minutes: number;
  total_delay_hours: number;
  avg_delay_minutes: number;
};

export type TimelinePoint = {
  year?: number;
  month?: number;
  day?: number;
  bucket: number;
  label: string;
  vehicle_type: "bus" | "subway";
  event_count: number;
  total_delay_minutes: number;
  avg_delay_minutes: number;
};

export type SpatiotemporalMapPoint = {
  stop_id: string;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
  vehicle_type: "bus" | "subway";
  hour_of_day: number;
  trip_events: number;
};
