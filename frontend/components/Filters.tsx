"use client";

import { VehicleType } from "../lib/types";

type Props = {
  routes: string[];
  selectedRoute: string;
  onRouteChange: (value: string) => void;
  timeWindow: number;
  onTimeWindowChange: (value: number) => void;
  vehicleType: VehicleType;
  onVehicleTypeChange: (value: VehicleType) => void;
};

export function Filters({
  routes,
  selectedRoute,
  onRouteChange,
  timeWindow,
  onTimeWindowChange,
  vehicleType,
  onVehicleTypeChange,
}: Props) {
  return (
    <div className="card filters">
      <div className="filter-group">
        <label>Route</label>
        <select value={selectedRoute} onChange={(e) => onRouteChange(e.target.value)}>
          <option value="all">All routes</option>
          {routes.map((route) => (
            <option key={route} value={route}>
              {route}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Time range</label>
        <select value={timeWindow} onChange={(e) => onTimeWindowChange(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Vehicle type</label>
        <select value={vehicleType} onChange={(e) => onVehicleTypeChange(e.target.value as VehicleType)}>
          <option value="all">All</option>
          <option value="bus">Bus</option>
          <option value="subway">Subway</option>
        </select>
      </div>
    </div>
  );
}
