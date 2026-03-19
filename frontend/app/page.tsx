import Link from "next/link";

export default function HomePage() {
  return (
    <main className="page">
      <div className="card">
        <h1>TTC Delay Analytics</h1>
        <p>Open the interactive dashboard to inspect route delays, rankings, and hourly heatmaps.</p>
        <Link href="/dashboard">Go to dashboard →</Link>
      </div>
    </main>
  );
}
