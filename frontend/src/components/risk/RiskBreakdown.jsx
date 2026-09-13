export default function RiskBreakdown({ factors = [] }) {
  return (
    <section className="panel" aria-labelledby="contributors-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Evidence received</span>
          <h2 id="contributors-title">Risk contributors</h2>
        </div>
      </div>
      {factors.length ? (
        <div className="factor-list">
          {factors.map((factor) => (
            <article className="factor" key={factor.key || factor.label}>
              <div className="factor-header">
                <div><strong>{factor.label}</strong><small>{factor.evidence}</small></div>
                <b>{Math.round(Number(factor.score) || 0)}</b>
              </div>
              <div className="factor-track"><span style={{ width: `${Math.min(100, Math.max(0, Number(factor.score) || 0))}%` }} /></div>
            </article>
          ))}
        </div>
      ) : <p className="empty-copy">No contributing factors were supplied by the risk pipeline.</p>}
    </section>
  );
}

