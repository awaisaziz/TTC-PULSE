import { InteractiveDashboard } from "../../components/InteractiveDashboard";

export default function BusPage() {
  return (
    <InteractiveDashboard
      vehicleFilter="bus"
      title="Bus Delay Analytics"
      subtitle="Interactive timeline analysis for TTC bus delays."
    />
  );
}
