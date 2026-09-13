import { useState } from "react";
import AlertPanel from "../components/alerts/AlertPanel";
import DashboardSidebar from "../components/layout/DashboardSidebar";
import RiskBreakdown from "../components/risk/RiskBreakdown";
import RiskGauge from "../components/risk/RiskGauge";
import HydrometEvidence from "../components/risk/HydrometEvidence";
import PageMeta from "../components/ui/PageMeta";
import DemoModeBanner from "../components/ui/DemoModeBanner";
import DataQualityPanel from "../features/member2-validation/DataQualityPanel";
import MonitoringPanel from "../features/member3-monitoring/MonitoringPanel";
import { useUnifiedAnalysis } from "../hooks/useUnifiedAnalysis";
import { USE_MOCK_ANALYSIS } from "../services/api";
import { formatUtcTimestamp } from "../utils/format";

const scenarios = ["normal", "watch", "warning", "critical"];

export default function Dashboard() {
  const [scenario, setScenario] = useState("critical");
  const { analysis, error, loading, refresh } = useUnifiedAnalysis("demo-dam-01", scenario);
  const modeLabel = USE_MOCK_ANALYSIS
    ? "simulation"
    : analysis?.data_mode === "HISTORICAL_REPLAY"
      ? "historical replay"
      : analysis?.data_mode === "LIVE"
        ? "live"
        : "operator input";

  return (
    <div className="dashboard-shell">
      <PageMeta title="Risk Overview | HydroSafe AI Command Center" description="Review the current HydroSafe AI risk state, evidence contributors and recommended response." path="/dashboard" />
      <DashboardSidebar />
      <main className="dashboard-page">
        {USE_MOCK_ANALYSIS && <DemoModeBanner />}
        {!USE_MOCK_ANALYSIS && analysis?.data_mode === "HISTORICAL_REPLAY" && (
          <div className="historical-mode-banner">
            <strong>Historical replay</strong>
            <span>This dashboard uses recorded observations from {analysis.source_observed_at ? formatUtcTimestamp(analysis.source_observed_at) : "an earlier monitoring period"}. It is not live telemetry.</span>
          </div>
        )}
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Demo Dam 01</span><span>/</span><strong>Risk overview</strong></nav>
        <header className="dashboard-header">
          <div><span className="eyebrow">Unified analysis / {modeLabel}</span><h1>Risk overview</h1><p>{USE_MOCK_ANALYSIS ? "Deterministic demonstration evidence from Demo Dam 01" : analysis?.source || "Latest synchronized evidence from Demo Dam 01"}</p></div>
          <div className="dashboard-controls">
            {USE_MOCK_ANALYSIS && <label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{scenarios.map((value) => <option key={value}>{value}</option>)}</select></label>}
            <button className="button button-secondary button-small" onClick={refresh} disabled={loading}>{loading ? "Refreshing…" : "Refresh evidence"}</button>
          </div>
        </header>

        {error && <section className="error-state" role="alert"><h2>Analysis unavailable</h2><p>{error}</p><button className="button button-secondary" onClick={refresh}>Try again</button></section>}
        {loading && !analysis && <section className="dashboard-loading" aria-live="polite"><div /><div /><span>Loading unified evidence…</span></section>}
        {analysis && (
          <>
            <AlertPanel risk={analysis.risk} generatedAt={analysis.generated_at} />
            <div className="dashboard-grid">
              <RiskGauge score={analysis.risk.score} level={analysis.risk.level} assessmentStatus={analysis.risk.assessment_status} />
              <RiskBreakdown factors={analysis.risk.contributing_factors} />
            </div>
            <HydrometEvidence assessment={analysis.risk.hydromet_assessment} />
            <DataQualityPanel quality={analysis.quality} />
            <MonitoringPanel analysis={analysis} />
          </>
        )}
      </main>
    </div>
  );
}
