import { InteractiveDashboard } from "../../components/InteractiveDashboard";

export default function SubwayPage() {
  return (
    <InteractiveDashboard
      vehicleFilter="subway"
      title="Subway Delay Analytics"
      subtitle="Interactive timeline analysis for TTC subway delays."
    />
  );
}
