const STATUS_LABELS = {
  NOT_SUPPLIED: "Not supplied",
  FRESH: "Fresh context",
  STALE: "Stale context",
  FUTURE_DATED: "Check timestamp",
};

export default function HydrometEvidence({ assessment = {} }) {
  const status = assessment.status || "NOT_SUPPLIED";
  const hasAnomaly = Boolean(assessment.anomaly_detected);
  const evidence = Array.isArray(assessment.anomaly_evidence) ? assessment.anomaly_evidence : [];

  return (
    <section className="panel hydromet-evidence" aria-labelledby="hydromet-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Environmental context</span>
          <h2 id="hydromet-title">Hydromet anomaly screen</h2>
        </div>
        <span className={`status-badge ${hasAnomaly ? "status-watch" : "status-normal"}`}>
          {hasAnomaly ? `${assessment.anomaly_severity || "Detected"} hydromet` : STATUS_LABELS[status] || status}
        </span>
      </div>
      <p>{assessment.summary || "No hydrometeorological context was supplied."}</p>
      {evidence.length > 0 && <ul>{evidence.map((item) => <li key={item}>{item}</li>)}</ul>}
      <small>Context contribution to structural risk: {Number(assessment.direct_risk_contribution) || 0} points. Structural corroboration is required.</small>
    </section>
  );
}
