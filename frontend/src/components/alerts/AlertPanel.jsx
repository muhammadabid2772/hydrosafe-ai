import { formatUtcTimestamp } from "../../utils/format";

const LEVEL_LABELS = {
  NORMAL: "Routine monitoring",
  WATCH: "Observation required",
  WARNING: "Engineer review required",
  CRITICAL: "Immediate response required",
  UNKNOWN: "Assessment pending",
};

export default function AlertPanel({ risk, generatedAt }) {
  const timestamp = formatUtcTimestamp(generatedAt);
  const isAssessed = risk.assessment_status === "ASSESSED";
  const visualLevel = isAssessed ? risk.level : "unknown";

  return (
    <section className={`alert-panel alert-${visualLevel.toLowerCase()}`} aria-live="polite" aria-labelledby="alert-title">
      <div className="alert-icon" aria-hidden="true">{isAssessed ? "!" : "?"}</div>
      <div className="alert-content">
        <span className="eyebrow">{isAssessed ? LEVEL_LABELS[risk.level] || LEVEL_LABELS.UNKNOWN : LEVEL_LABELS.UNKNOWN}</span>
        <h2 id="alert-title">{risk.warning_message}</h2>
        <div className="recommended-action">
          <span>Recommended next action</span>
          <p>{risk.recommended_next_action}</p>
        </div>
        <small>{isAssessed ? "Assessment" : "Evidence review"} received {timestamp}. Confirm critical decisions with an authorized dam safety engineer.</small>
      </div>
    </section>
  );
}
