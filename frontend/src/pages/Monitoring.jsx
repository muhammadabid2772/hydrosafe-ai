import DashboardSidebar from "../components/layout/DashboardSidebar";
import DemoModeBanner from "../components/ui/DemoModeBanner";
import PageMeta from "../components/ui/PageMeta";
import DataQualityPanel from "../features/member2-validation/DataQualityPanel";
import MonitoringPanel from "../features/member3-monitoring/MonitoringPanel";
import { useUnifiedAnalysis } from "../hooks/useUnifiedAnalysis";
import { USE_MOCK_ANALYSIS } from "../services/api";
import { formatUtcTimestamp } from "../utils/format";

export default function Monitoring() {
  const { analysis, error, loading, refresh } = useUnifiedAnalysis("demo-dam-01", "critical");
  const seriesCount = analysis?.trends?.series?.length || 0;

  return (
    <div className="dashboard-shell">
      <PageMeta title="Monitoring Trends | HydroSafe AI" description="Review validated structural monitoring trends, observation windows and sensor health." path="/dashboard/monitoring" />
      <DashboardSidebar />
      <main className="dashboard-page monitoring-page">
        {USE_MOCK_ANALYSIS && <DemoModeBanner />}
        {!USE_MOCK_ANALYSIS && analysis?.data_mode === "HISTORICAL_REPLAY" && (
          <div className="historical-mode-banner">
            <strong>Historical replay</strong>
            <span>Recorded observations from {analysis.source_observed_at ? formatUtcTimestamp(analysis.source_observed_at) : "an earlier monitoring period"}. This is not live telemetry.</span>
          </div>
        )}
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Demo Dam 01</span><span>/</span><strong>Monitoring trends</strong></nav>
        <header className="dashboard-header">
          <div><span className="eyebrow">Structural monitoring</span><h1>Monitoring trends</h1><p>Validated instrument behaviour, observation windows and evidence from the unified analysis pipeline.</p></div>
          <div className="monitoring-header-actions">
            {analysis?.trends?.available && <span className="series-count"><strong>{seriesCount}</strong><small>series analysed</small></span>}
            <button className="button button-secondary button-small" onClick={refresh} disabled={loading}>{loading ? "Refreshing…" : "Refresh trends"}</button>
          </div>
        </header>

        {error && <section className="error-state" role="alert"><h2>Monitoring unavailable</h2><p>{error}</p><button className="button button-secondary" onClick={refresh}>Try again</button></section>}
        {loading && !analysis && <section className="dashboard-loading" aria-live="polite"><div /><div /><span>Loading validated monitoring data…</span></section>}
        {analysis && (
          <>
            <DataQualityPanel quality={analysis.quality} />
            <MonitoringPanel analysis={analysis} />
          </>
        )}
      </main>
    </div>
  );
}
