import HealthStatus from "./health-status";
import SummaryForm from "./summary-form";

export default function Home() {
  return (
    <main>
      <h1>Video Soru Üretici</h1>
      <p className="muted">YouTube ders videolarından doğrulanabilir alıştırma soruları.</p>
      <HealthStatus />
      <SummaryForm />
    </main>
  );
}
