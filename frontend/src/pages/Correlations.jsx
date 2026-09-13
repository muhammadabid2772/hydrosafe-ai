import DashboardSidebar from "../components/layout/DashboardSidebar";
import PageMeta from "../components/ui/PageMeta";
import { useUnifiedAnalysis } from "../hooks/useUnifiedAnalysis";

export default function Correlations() {
  const { analysis, error, loading, refresh } = useUnifiedAnalysis("demo-dam-01", "critical");
  const evidence = analysis?.correlations || [];
  const detected = evidence.filter((item) => item.correlation_detected);

  return (
    <div className="dashboard-shell">
      <PageMeta title="Hydro-Structural Correlations | HydroSafe AI" description="Review Member 5 correlation evidence and cross-signal reasoning." path="/dashboard/correlations" />
      <DashboardSidebar />
      <main className="dashboard-page correlation-page">
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Demo Dam 01</span><span>/</span><strong>Correlations</strong></nav>
        <header className="dashboard-header">
          <div><span className="eyebrow">Agent 5 / evidence engine</span><h1>Hydro-structural correlations</h1><p>Paired-series Pearson evidence and temporal cross-signal reasoning. Association is never presented as causation.</p></div>
          <button className="button button-secondary button-small" onClick={refresh} disabled={loading}>{loading ? "Refreshing…" : "Refresh evidence"}</button>
        </header>

        {error && <section className="error-state" role="alert"><h2>Correlation evidence unavailable</h2><p>{error}</p></section>}
        {loading && !analysis && <section className="dashboard-loading"><span>Loading correlation evidence…</span></section>}
        {analysis && (
          <>
            <section className="correlation-summary panel">
              <div><span className="eyebrow">Current result</span><h2>{detected.length ? `${detected.length} correlated pattern${detected.length === 1 ? "" : "s"} detected` : "No material correlated pattern detected"}</h2></div>
              <dl><div><dt>Evidence records</dt><dd>{evidence.length}</dd></div><div><dt>Detected</dt><dd>{detected.length}</dd></div><div><dt>Risk contribution</dt><dd>{analysis.risk.contributing_factors.find((item) => item.key === "correlation")?.score ?? 0}/100</dd></div></dl>
            </section>
            <section className="correlation-list">
              {evidence.length === 0 ? (
                <article className="panel correlation-empty"><span className="eyebrow">Insufficient paired evidence</span><h2>Correlation needs more than one aligned signal.</h2><p>The current historical replay contains a single structural series, so Agent 5 correctly refuses to invent a relationship. Upload or submit multiple aligned series, or supply hydrometeorological context with structural evidence, through the unified API.</p></article>
              ) : evidence.map((item, index) => (
                <article className={`panel correlation-card ${item.correlation_detected ? "detected" : ""}`} key={`${item.evidence_type}-${index}`}>
                  <div className="correlation-card-head"><span>{item.evidence_type?.replaceAll("_", " ")}</span><strong>{item.correlation_detected ? "DETECTED" : "OBSERVED"}</strong></div>
                  <h2>{item.related_parameters?.join(" ↔ ") || "Cross-signal evidence"}</h2>
                  <p>{item.explanation}</p>
                  <dl><div><dt>Score</dt><dd>{Number(item.score || 0).toFixed(1)}</dd></div><div><dt>Confidence</dt><dd>{Math.round(Number(item.confidence || 0) * 100)}%</dd></div>{item.coefficient !== null && item.coefficient !== undefined && <div><dt>Pearson r</dt><dd>{Number(item.coefficient).toFixed(2)}</dd></div>}{item.paired_points && <div><dt>Paired points</dt><dd>{item.paired_points}</dd></div>}</dl>
                </article>
              ))}
            </section>
            <section className="panel correlation-boundary"><span className="eyebrow">Engineering boundary</span><p>Correlation evidence supports investigation priority. It does not prove that reservoir, rainfall, seepage, pressure, displacement, or any other signal caused another measurement to change.</p></section>
          </>
        )}
      </main>
    </div>
  );
}
