import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Database,
  Droplets,
  Gauge,
  RotateCcw,
  ShieldCheck,
  Thermometer,
  Waves,
} from "lucide-react";
import DashboardSidebar from "../components/layout/DashboardSidebar";
import PageMeta from "../components/ui/PageMeta";
import {
  buildAnomalyRequest,
  CONDITION_FIELDS,
  DEFAULT_CONDITIONS,
  severityTone,
  validateConditions,
} from "../features/member4-anomaly/anomalyForm";
import { assessMember4Anomaly } from "../services/anomalyService";
import { formatUnit, formatUtcTimestamp } from "../utils/format";

const icons = {
  reservoir_level: Waves,
  tailwater: Droplets,
  inflow: Activity,
  rainfall: Droplets,
  temperature: Thermometer,
};

function localDateTimeValue() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 16);
}

function ParameterTable({ parameters }) {
  return (
    <div className="anomaly-table-wrap">
      <table className="anomaly-table">
        <caption>Statistical screening flags a parameter at |z| ≥ 3. Isolation Forest may also identify a combined multivariable deviation.</caption>
        <thead><tr><th>Parameter</th><th>Current</th><th>Historical range</th><th>Deviation</th><th>Status</th></tr></thead>
        <tbody>
          {parameters.map((item) => (
            <tr key={item.metric}>
              <th scope="row">{item.label}</th>
              <td>{item.value.toLocaleString()} <small>{formatUnit(item.unit)}</small></td>
              <td>{item.historical_min.toLocaleString()}–{item.historical_max.toLocaleString()} <small>{formatUnit(item.unit)}</small></td>
              <td><strong>{item.abs_z.toFixed(2)}</strong> <small>|z|</small></td>
              <td><span className={`parameter-state ${item.flagged ? "flagged" : "within"}`}>{item.flagged ? "Outside baseline" : "Within baseline"}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AnomalyCharts({ parameters }) {
  const maximumDeviation = Math.max(3.5, ...parameters.map((item) => Number(item.abs_z) || 0));

  return (
    <section className="panel anomaly-charts" aria-labelledby="anomaly-charts-title">
      <div className="section-heading">
        <div><span className="eyebrow">Visual analysis</span><h2 id="anomaly-charts-title">Deviation and baseline position</h2></div>
        <span className="chart-legend"><i /> Alert threshold |z| = 3</span>
      </div>
      <div className="anomaly-chart-grid">
        <figure className="deviation-chart">
          <figcaption><strong>Standard deviation profile</strong><span>Distance from historical mean</span></figcaption>
          <div className="deviation-plot">
            {parameters.map((item) => (
              <div className="deviation-row" key={item.metric}>
                <span>{item.label}</span>
                <div className="deviation-track">
                  <i className="deviation-threshold" style={{ left: `${(3 / maximumDeviation) * 100}%` }} />
                  <b className={item.flagged ? "flagged" : ""} style={{ width: `${Math.max(1.5, (item.abs_z / maximumDeviation) * 100)}%` }} />
                </div>
                <strong>{item.abs_z.toFixed(2)}</strong>
              </div>
            ))}
          </div>
        </figure>
        <figure className="baseline-chart">
          <figcaption><strong>Position within observed range</strong><span>Markers at either edge indicate an out-of-range value</span></figcaption>
          <div className="baseline-plot">
            {parameters.map((item) => {
              const spread = item.historical_max - item.historical_min || 1;
              const rawPosition = ((item.value - item.historical_min) / spread) * 100;
              const position = Math.min(100, Math.max(0, rawPosition));
              const outside = rawPosition < 0 || rawPosition > 100;
              return (
                <div className="baseline-row" key={item.metric}>
                  <div><span>{item.label}</span><strong>{item.value.toLocaleString()} {formatUnit(item.unit)}</strong></div>
                  <div className={`baseline-track ${outside ? "outside" : ""}`}><i style={{ left: `${position}%` }} /></div>
                  <small><span>{item.historical_min.toLocaleString()}</span><span>{item.historical_max.toLocaleString()}</span></small>
                </div>
              );
            })}
          </div>
        </figure>
      </div>
    </section>
  );
}

function Results({ result }) {
  if (!result) {
    return (
      <section className="panel anomaly-empty" aria-live="polite">
        <Gauge aria-hidden="true" />
        <span className="eyebrow">Awaiting assessment</span>
        <h2>Enter the latest field conditions</h2>
        <p>The detector will compare all five values with the shared 2019–2026 historical baseline.</p>
      </section>
    );
  }

  const anomaly = result.anomaly;
  const risk = result.risk;
  const tone = severityTone(anomaly.severity);
  const SeverityIcon = anomaly.anomaly ? AlertTriangle : CheckCircle2;
  const requiresSourceVerification = anomaly.parameters.filter(
    (item) => item.value < item.historical_min || item.value > item.historical_max,
  );
  const riskAssessed = risk.assessment_status === "ASSESSED";
  const missingEntries = Object.entries(anomaly.history_quality.missing_by_parameter || {});

  return (
    <div className="anomaly-results" aria-live="polite">
      <section className={`panel anomaly-verdict verdict-${tone}`}>
        <div className="verdict-icon"><SeverityIcon aria-hidden="true" /></div>
        <div className="verdict-copy">
          <span className="eyebrow">Hydrometeorological statistical screen</span>
          <div className="verdict-title"><h2>{anomaly.anomaly ? `${anomaly.severity} hydrometeorological anomaly detected` : "No significant hydrometeorological anomaly"}</h2></div>
          {requiresSourceVerification.length > 0 && <div className="source-verification"><AlertTriangle aria-hidden="true" /><span><strong>Source verification required</strong>{requiresSourceVerification.map((item) => item.label).join(", ")} {requiresSourceVerification.length === 1 ? "is" : "are"} outside the observed historical range. Confirm units, reporting period and source entry before interpretation.</span></div>}
          <p>{anomaly.engineering_interpretation}</p>
        </div>
        <dl className="verdict-metrics">
          <div><dt>Maximum deviation</dt><dd>{anomaly.max_abs_z.toFixed(2)} <small>|z|</small></dd></div>
          <div><dt>Isolation Forest</dt><dd>{anomaly.isolation_forest_flag ? "Flagged" : "Clear"}</dd></div>
          <div><dt>Structural risk points</dt><dd>{anomaly.direct_structural_risk_contribution}</dd></div>
        </dl>
      </section>

      <section className="panel anomaly-guardrail">
        <ShieldCheck aria-hidden="true" />
        <div><span className="eyebrow">Assessment boundary</span><h2>{riskAssessed ? `${risk.level} · ${risk.score.toFixed(1)}/100` : "Structural risk not assessed"}</h2><p>{riskAssessed ? risk.warning_message : "Validated structural readings, trends, anomalies or correlations were not supplied."} Hydrometeorological evidence remains contextual until structural instruments corroborate it.</p></div>
      </section>

      <section className="panel anomaly-parameters">
        <div className="section-heading"><div><span className="eyebrow">Five-parameter analysis</span><h2>Deviation from historical behaviour</h2></div><span className="owner-label">Z-SCORE + ISOLATION FOREST</span></div>
        <ParameterTable parameters={anomaly.parameters} />
      </section>

      <AnomalyCharts parameters={anomaly.parameters} />

      <div className="anomaly-detail-grid">
        <section className="panel history-quality">
          <div className="section-heading"><div><span className="eyebrow">Reference data</span><h2>Historical coverage</h2></div><Database aria-hidden="true" /></div>
          <dl>
            <div><dt>Period</dt><dd>{anomaly.history_quality.date_start} — {anomaly.history_quality.date_end}</dd></div>
            <div><dt>Available rows</dt><dd>{anomaly.history_quality.complete_rows.toLocaleString()} / {anomaly.history_quality.raw_rows.toLocaleString()}</dd></div>
          </dl>
          {missingEntries.length > 0 && <div className="missing-values"><strong>Missing values by parameter</strong><ul>{missingEntries.map(([metric, count]) => <li key={metric}><span>{metric.replaceAll("_", " ")}</span><b>{count.toLocaleString()}</b></li>)}</ul></div>}
          {anomaly.history_quality.warnings.map((warning) => <p className="quality-warning" key={warning}><AlertTriangle aria-hidden="true" />{warning}</p>)}
        </section>
        <section className="panel model-limitations">
          <span className="eyebrow">Engineering boundary</span><h2>Use this as screening evidence</h2>
          <ul>{anomaly.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>
      </div>
    </div>
  );
}

export default function AnomalyDetector() {
  const [values, setValues] = useState({ ...DEFAULT_CONDITIONS });
  const [observedAt, setObservedAt] = useState(localDateTimeValue);
  const [structure, setStructure] = useState("ACCRD");
  const [errors, setErrors] = useState({});
  const [requestError, setRequestError] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const flaggedCount = useMemo(() => result?.anomaly?.parameters?.filter((item) => item.flagged).length || 0, [result]);

  const submit = async (event) => {
    event.preventDefault();
    const nextErrors = validateConditions(values);
    if (!observedAt || Number.isNaN(new Date(observedAt).getTime())) nextErrors.observedAt = "Choose a valid observation time.";
    setErrors(nextErrors);
    setRequestError("");
    if (Object.keys(nextErrors).length) return;
    setLoading(true);
    try {
      const payload = buildAnomalyRequest({ values, observedAt, structure });
      setResult(await assessMember4Anomaly(payload));
    } catch (error) {
      setRequestError(error.message || "The anomaly assessment could not be completed.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setValues({ ...DEFAULT_CONDITIONS });
    setObservedAt(localDateTimeValue());
    setErrors({});
    setRequestError("");
    setResult(null);
  };

  return (
    <div className="dashboard-shell">
      <PageMeta title="Anomaly Detector | HydroSafe AI" description="Screen reservoir level, tailwater, inflow, rainfall and temperature against the shared historical baseline." path="/dashboard/anomalies" />
      <DashboardSidebar />
      <main className="dashboard-page anomaly-page">
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Demo Dam 01</span><span>/</span><strong>Anomaly detector</strong></nav>
        <header className="dashboard-header anomaly-header">
          <div><span className="eyebrow">Hydrometeorological screening</span><h1>Anomaly detector</h1><p>Compare current conditions with 2,800 historical observations from 2019–2026.</p></div>
          <div className="baseline-chip"><Database aria-hidden="true" /><span><small>TEAM-APPROVED BASELINE</small><strong>Locked · 5 parameters</strong></span></div>
        </header>

        <div className="anomaly-workbench">
          <form className="panel anomaly-form" onSubmit={submit} noValidate>
            <div className="section-heading"><div><span className="eyebrow">Current observation</span><h2>Field conditions</h2></div><span className="owner-label">OPERATOR ENTRY</span></div>
            <div className="input-provenance"><AlertTriangle aria-hidden="true" /><span><strong>Manual hydromet observation</strong>Values are screened against the shared history. For ACCRD, the risk result also reuses the latest validated structural evidence from the unified API when available.</span></div>
            <label className="anomaly-select"><span>Structure</span><select value={structure} onChange={(event) => setStructure(event.target.value)}><option value="ACCRD">ACCRD · Dam wall</option><option value="POWER_HOUSE">Power House</option><option value="POWER_INTAKE">Power Intake</option></select></label>
            <label className="anomaly-input timestamp-input"><span><CalendarDays aria-hidden="true" />Observed at</span><input type="datetime-local" value={observedAt} onChange={(event) => setObservedAt(event.target.value)} aria-invalid={Boolean(errors.observedAt)} />{errors.observedAt && <small className="field-error">{errors.observedAt}</small>}</label>
            <div className="condition-fields">
              {CONDITION_FIELDS.map((field) => {
                const FieldIcon = icons[field.key];
                return <label className="anomaly-input" key={field.key}><span><FieldIcon aria-hidden="true" />{field.label}<small>{field.unit}</small></span><input type="number" inputMode="decimal" step={field.step} min={field.min} value={values[field.key]} onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))} aria-invalid={Boolean(errors[field.key])} />{errors[field.key] && <small className="field-error">{errors[field.key]}</small>}</label>;
              })}
            </div>
            {requestError && <div className="anomaly-request-error" role="alert"><AlertTriangle aria-hidden="true" /><span><strong>Assessment unavailable</strong>{requestError}</span></div>}
            <div className="anomaly-form-actions"><button type="submit" className="button button-primary" disabled={loading}>{loading ? "Analysing…" : "Run anomaly detection"}</button><button type="button" className="button button-secondary reset-button" onClick={reset} disabled={loading}><RotateCcw aria-hidden="true" />Reset</button></div>
            <p className="form-footnote"><ShieldCheck aria-hidden="true" />Results support engineering review; they do not replace approved action levels.</p>
          </form>

          <div className="anomaly-output">
            {result && <div className="result-summary-line"><span>{flaggedCount} parameter{flaggedCount === 1 ? "" : "s"} outside baseline</span><time dateTime={result.anomaly.observed_at}>{formatUtcTimestamp(result.anomaly.observed_at)}</time></div>}
            <Results result={result} />
          </div>
        </div>
      </main>
    </div>
  );
}
