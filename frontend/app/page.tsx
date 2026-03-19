import { InteractiveDashboard } from "../components/InteractiveDashboard";

export default function HomePage() {
  return (
    <InteractiveDashboard
      vehicleFilter="all"
      title="TTC Delay Analytics"
      subtitle="Bus and Subway delay statistics with interactive year, month, and day timeline analysis."
    />
  );
}
