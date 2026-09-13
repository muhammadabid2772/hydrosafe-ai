import { Activity, AlertTriangle } from "lucide-react";
import { formatUnit, formatUtcTimestamp } from "../../utils/format";

function numberOrDash(value, digits = 2) {
  return Number.isFinite(Number(value)) && value !== null ? Number(value).toFixed(digits) : "—";
}

function TrendChart({ series }) {
  const points = (series.chart_points || []).filter((point) => Number.isFinite(Number(point.value)));
  if (points.length < 2) return <div className="trend-chart-empty">Chart points unavailable for this series.</div>;
  const values = points.map((point) => Number(point.value));
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  const coordinates = values.map((value, index) => {
    const x = (index / (values.length - 1)) * 600;
    const y = 150 - ((value - minimum) / spread) * 120;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const last = coordinates.split(" ").at(-1).split(",");
  return (
    <div className="trend-chart">
      <svg viewBox="0 0 600 180" role="img" aria-label={`${series.instrument_id} ${series.trend} trend chart`}>
        <line x1="0" y1="30" x2="600" y2="30" /><line x1="0" y1="90" x2="600" y2="90" /><line x1="0" y1="150" x2="600" y2="150" />
        <polyline points={coordinates} />
        <circle cx={last[0]} cy={last[1]} r="5" />
      </svg>
      <div><span>{formatUtcTimestamp(points[0].timestamp)}</span><span>{formatUtcTimestamp(points.at(-1).timestamp)}</span></div>
    </div>
  );
}

export default function MonitoringPanel({ analysis }) {
  const trends = analysis?.trends;
  const series = trends?.series || [];
  return (
    <section id="monitoring" className="panel monitoring-slot" aria-labelledby="monitoring-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Trend intelligence</span>
          <h2 id="monitoring-title">Monitoring trends</h2>
        </div>
        <span className="owner-label">{trends?.status || "UNAVAILABLE"}</span>
      </div>
      {!trends?.available ? (
        <div className="empty-module"><AlertTriangle aria-hidden="true" /><span>TREND DATA UNAVAILABLE</span><p>{trends?.message || "No validated time series was returned by the unified API."}</p></div>
      ) : (
        <div className="trend-series-list">
          {series.map((item) => (
            <article className="trend-series" key={`${item.instrument_id}-${item.metric}`}>
              <header><div><Activity aria-hidden="true" /><span><small>{item.instrument_id}</small><strong>{String(item.metric).replaceAll("_", " ")}</strong></span></div><b className={`trend-${item.trend}`}>{item.trend}</b></header>
              <TrendChart series={item} />
              <dl>
                <div><dt>Change</dt><dd>{numberOrDash(item.percentage_change)}%</dd></div>
                <div><dt>Rate</dt><dd>{numberOrDash(item.rate_of_change, 4)} <small>{formatUnit(item.unit)} {item.rate_unit === "per_day" ? "/ day" : "/ observation"}</small></dd></div>
                <div><dt>Confidence</dt><dd>{item.confidence === null || item.confidence === undefined ? "—" : `${Math.round(Number(item.confidence) * 100)}%`}</dd></div>
                <div><dt>Trend score</dt><dd>{numberOrDash(item.score, 1)}<small> / 100</small></dd></div>
                <div><dt>Sustained</dt><dd>{typeof item.sustained === "boolean" ? (item.sustained ? "Yes" : "No") : "—"}</dd></div>
                <div><dt>Acceleration</dt><dd>{typeof item.sudden_acceleration === "boolean" ? (item.sudden_acceleration ? "Detected" : "None") : "—"}</dd></div>
                <div><dt>Window</dt><dd>{item.time_window ?? "—"} <small>observations</small></dd></div>
              </dl>
              <p>{item.evidence || "Trend evidence was not supplied."}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
