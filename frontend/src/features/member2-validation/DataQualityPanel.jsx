import { AlertTriangle, CheckCircle2, Database, ShieldQuestion } from "lucide-react";

function valueOrDash(value, suffix = "") {
  return Number.isFinite(Number(value)) && value !== null ? `${Number(value).toLocaleString()}${suffix}` : "—";
}

export default function DataQualityPanel({ quality }) {
  const available = quality?.available === true;
  const HealthIcon = available ? CheckCircle2 : ShieldQuestion;
  const sensors = Object.entries(quality?.sensor_health || {});
  const reference = quality?.reference_dataset;

  return (
    <section className="panel quality-panel" aria-labelledby="quality-title">
      <div className="section-heading">
        <div><span className="eyebrow">Validated telemetry</span><h2 id="quality-title">Data quality and sensor health</h2></div>
        <span className={`status-badge status-${available && quality.quality_status === "GOOD" ? "normal" : available ? "watch" : "unknown"}`}>
          {available ? quality.quality_status : "UNAVAILABLE"}
        </span>
      </div>

      {!available ? (
        <div className="quality-unavailable"><ShieldQuestion aria-hidden="true" /><div><strong>Validation result unavailable</strong><p>{quality?.warning || "No validation dataset was supplied to the unified analysis pipeline."}</p></div></div>
      ) : (
        <>
          <div className="quality-summary">
            <div className="quality-score"><HealthIcon aria-hidden="true" /><span><strong>{valueOrDash(quality.score)}</strong><small>/ 100 quality</small></span></div>
            <dl>
              <div><dt>Received</dt><dd>{valueOrDash(quality.total_records)}</dd></div>
              <div><dt>Validated</dt><dd>{valueOrDash(quality.valid_count)}</dd></div>
              <div><dt>Excluded</dt><dd>{valueOrDash(quality.flagged_count)}</dd></div>
              <div><dt>Scope</dt><dd>{quality.scope || "—"}</dd></div>
            </dl>
          </div>
          {quality.warning && <p className="quality-notice"><AlertTriangle aria-hidden="true" />{quality.warning}</p>}
          <div className="sensor-health-grid">
            {sensors.length ? sensors.map(([sensor, health]) => (
              <article key={sensor}>
                <span>{sensor.replaceAll("_", " ")}</span>
                <strong className={`health-${String(health.status || "unknown").toLowerCase()}`}>{health.status || "UNKNOWN"}</strong>
                <small>{valueOrDash(health.total)} readings · {valueOrDash((health.missing_ratio || 0) * 100, "%")} missing</small>
              </article>
            )) : <p className="empty-copy">No per-sensor health indicators were returned.</p>}
          </div>
        </>
      )}

      {reference && (
        <div className="reference-quality"><Database aria-hidden="true" /><div><span>Hydromet reference dataset</span><strong>{valueOrDash(reference.score)}/100 · {reference.quality_status || "UNKNOWN"}</strong><small>{valueOrDash(reference.valid_count)} of {valueOrDash(reference.total_records)} records validated. This quality is displayed separately and is not applied to structural risk.</small></div></div>
      )}
    </section>
  );
}
