const LEVEL_COLORS = {
  NORMAL: "#35d3c8",
  WATCH: "#f5bf50",
  WARNING: "#f28b45",
  CRITICAL: "#ef5f63",
  UNKNOWN: "#8295a5",
};

export default function RiskGauge({ score, level, assessmentStatus = "ASSESSED" }) {
  const isAssessed = assessmentStatus === "ASSESSED";
  const displayedScore = isAssessed && Number.isFinite(score) ? score : 0;
  const visualLevel = isAssessed ? level : "UNKNOWN";
  const color = LEVEL_COLORS[visualLevel] || LEVEL_COLORS.UNKNOWN;
  const radius = 82;
  const circumference = Math.PI * radius;
  const progress = (displayedScore / 100) * circumference;

  return (
    <section className="panel risk-gauge-card" aria-labelledby="risk-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">{isAssessed ? "Risk assessment" : "Assessment pending"}</span>
          <h2 id="risk-title">Current risk</h2>
        </div>
        <span className={`status-badge status-${visualLevel.toLowerCase()}`}>{isAssessed ? level : "NOT ASSESSED"}</span>
      </div>
      <div className="gauge" style={{ "--risk-color": color }}>
        <svg viewBox="0 0 210 122" role="img" aria-label={isAssessed ? `${level} risk, ${score ?? "unavailable"} out of 100` : "Structural risk not assessed"}>
          <path className="gauge-track" d="M23 105a82 82 0 0 1 164 0" pathLength={circumference} />
          <path
            className="gauge-value"
            d="M23 105a82 82 0 0 1 164 0"
            pathLength={circumference}
            style={{ strokeDasharray: `${progress} ${circumference}` }}
          />
        </svg>
        <div className="gauge-number"><strong>{isAssessed ? score ?? "—" : "—"}</strong><span>{isAssessed ? "/ 100" : "Awaiting evidence"}</span></div>
      </div>
      <div className="risk-scale" aria-hidden="true">
        <span>NORMAL</span><span>WATCH</span><span>WARNING</span><span>CRITICAL</span>
      </div>
    </section>
  );
}
