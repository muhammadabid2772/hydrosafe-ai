import { useEffect, useState } from "react";
import DashboardSidebar from "../components/layout/DashboardSidebar";
import PageMeta from "../components/ui/PageMeta";
import { useUnifiedAnalysis } from "../hooks/useUnifiedAnalysis";
import { generateReport, listReports } from "../services/reportService";
import { formatUtcTimestamp } from "../utils/format";

function downloadReport(report) {
  const blob = new Blob([report.content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${report.report_id}.txt`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const { analysis, error: analysisError, loading: analysisLoading } = useUnifiedAnalysis("demo-dam-01", "critical");
  const [reports, setReports] = useState([]);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState({ loading: false, error: "" });

  useEffect(() => {
    listReports().then((items) => { setReports(items); if (items[0]) setSelected(items[0]); }).catch(() => {});
  }, []);

  async function create() {
    if (!analysis) return;
    setStatus({ loading: true, error: "" });
    try {
      const report = await generateReport(analysis);
      setReports((current) => [report, ...current.filter((item) => item.report_id !== report.report_id)]);
      setSelected(report);
    } catch (error) {
      setStatus({ loading: false, error: error.message || "Report generation failed." });
      return;
    }
    setStatus({ loading: false, error: "" });
  }

  return (
    <div className="dashboard-shell">
      <PageMeta title="Engineering Reports | HydroSafe AI" description="Generate and review explainable HydroSafe engineering monitoring reports." path="/dashboard/reports" />
      <DashboardSidebar />
      <main className="dashboard-page reports-page">
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Demo Dam 01</span><span>/</span><strong>Reports</strong></nav>
        <header className="dashboard-header">
          <div><span className="eyebrow">Explainable reporting</span><h1>Engineering reports</h1><p>Generate a grounded report from the same synchronized evidence used by the risk engine.</p></div>
          <button className="button button-primary button-small" onClick={create} disabled={!analysis || analysisLoading || status.loading}>{status.loading ? "Generating…" : "Generate report"}</button>
        </header>
        {(analysisError || status.error) && <div className="anomaly-request-error" role="alert">{analysisError || status.error}</div>}
        <div className="reports-layout">
          <aside className="panel report-history"><span className="eyebrow">Saved reports</span><h2>History</h2>{reports.length === 0 ? <p>No generated reports yet.</p> : reports.map((report) => <button key={report.report_id} className={selected?.report_id === report.report_id ? "active" : ""} onClick={() => setSelected(report)}><strong>{report.risk_level} · {Number(report.risk_score).toFixed(1)}</strong><span>{report.structure}</span><small>{formatUtcTimestamp(report.created_at)}</small></button>)}</aside>
          <section className="panel report-preview">
            {!selected ? <div className="report-empty"><span className="eyebrow">Ready to generate</span><h2>Create the first synchronized report.</h2><p>The report will include validation, trends, Agent 4 anomalies, Agent 5 correlations, Agent 6 risk reasoning, recommended action, and safety limitations.</p></div> : <><div className="report-preview-head"><div><span className="eyebrow">{selected.ai_enhanced ? "AI enhanced · grounded" : "Deterministic grounded report"}</span><h2>{selected.title}</h2><p>{formatUtcTimestamp(selected.created_at)}</p></div><button className="button button-secondary button-small" onClick={() => downloadReport(selected)}>Download TXT</button></div><pre>{selected.content}</pre></>}
          </section>
        </div>
      </main>
    </div>
  );
}
