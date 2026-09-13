import { Link } from "react-router-dom";
import {
  Activity, ArrowDown, ArrowUpRight, BellRing, CheckCircle2, CloudRain,
  Database, Gauge, Network, ScanSearch, ShieldCheck, UserCheck, Waves,
} from "lucide-react";
import CharacterReveal from "../components/ui/CharacterReveal";
import PageMeta from "../components/ui/PageMeta";
import { useAuth } from "../contexts/AuthContext";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const features = [
  { number: "01", icon: Database, title: "Trust the data first", text: "Missing values, duplicate timestamps, stale sensors and impossible measurements are surfaced before analysis begins.", owner: "Data quality agent", className: "feature-primary" },
  { number: "02", icon: Activity, title: "See direction, not noise", text: "Rolling change and slope reveal whether reservoir, inflow, seepage and pressure are stable or accelerating.", owner: "Trend intelligence" },
  { number: "03", icon: ScanSearch, title: "Catch unusual behaviour", text: "Every current reading is checked against that instrument’s own historical pattern, not a generic rule.", owner: "Anomaly agent" },
  { number: "04", icon: Network, title: "Connect cause and response", text: "Hydrology, weather and nearby sensors are compared so operators can distinguish a normal response from an inconsistency.", owner: "Correlation engine" },
  { number: "05", icon: BellRing, title: "Move from evidence to action", text: "One clear risk state keeps the score, the strongest evidence and the engineer’s next verification step together.", owner: "Risk and warning" },
];

const workflow = [
  { number: "01", icon: Waves, title: "Collect", text: "Hydrological and structural readings arrive with timestamps, units and sensor identity." },
  { number: "02", icon: ShieldCheck, title: "Verify", text: "Five specialist agents validate quality, movement, anomalies and relationships." },
  { number: "03", icon: Gauge, title: "Interpret", text: "The risk layer ranks the evidence and explains the current operational state." },
  { number: "04", icon: UserCheck, title: "Decide", text: "The authorized engineer receives a traceable recommendation—not an unexplained prediction." },
];

const structuredData = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "HydroSafe AI",
  applicationCategory: "MonitoringApplication",
  operatingSystem: "Web",
  description: "Agentic hydrological and dam safety monitoring, anomaly detection and early warning interface.",
};

export default function LandingPage() {
  const { user } = useAuth();
  useRevealOnScroll();

  return (
    <main className="landing-page">
      <PageMeta title="HydroSafe AI | Dam Safety Intelligence" description="HydroSafe AI validates dam monitoring data, detects abnormal behavior, connects hydrological and structural evidence, and presents explainable early warnings." path="/" structuredData={structuredData} />

      <section className="landing-hero" id="home">
        <img className="hero-photo" src="/assets/hydrosafe-dam-hero.webp" alt="Hydroelectric dam and mountain reservoir monitored by HydroSafe AI" fetchPriority="high" />
        <div className="hero-shade" aria-hidden="true" />
        <div className="hero-copy">
          <div className="hero-status"><span><i /> System demonstration ready</span><small>03 structures connected</small></div>
          <span className="kicker"><ShieldCheck size={15} /> Explainable dam safety intelligence</span>
          <h1><CharacterReveal text="See the signal." /><CharacterReveal text="Before it becomes a warning." className="accent-line" /></h1>
          <p>HydroSafe AI brings reservoir conditions, instrument behaviour and risk evidence into one operational view—so teams can understand what changed, why it matters and what to verify next.</p>
          <div className="hero-actions">
            <Link className="button button-primary button-arrow" to={user ? "/dashboard" : "/signup"}>
              {user ? "Open command center" : "Explore the live demo"}<ArrowUpRight size={17} />
            </Link>
            <a className="text-link" href="#about">How the system thinks <ArrowDown size={16} /></a>
          </div>
        </div>

        <aside className="hero-console" aria-label="Example synchronized monitoring snapshot">
          <header><div><span className="console-live"><i /> synchronized snapshot</span><strong>Karot / ACCRD</strong></div><small>08:42 UTC</small></header>
          <div className="console-risk">
            <div><small>EXPLAINABLE RISK</small><strong>24</strong><span>/ 100</span></div>
            <span className="risk-normal"><CheckCircle2 size={15} /> NORMAL</span>
          </div>
          <svg className="console-chart" viewBox="0 0 440 104" role="img" aria-label="Stable monitoring trend over the latest observations">
            <defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#36ddd0" stopOpacity=".28"/><stop offset="1" stopColor="#36ddd0" stopOpacity="0"/></linearGradient></defs>
            <path className="chart-area" d="M0 83 C34 75 50 77 76 69 S125 77 154 58 S205 62 232 48 S279 53 309 37 S359 41 390 28 S423 26 440 19 L440 104 L0 104Z" />
            <path className="chart-line" d="M0 83 C34 75 50 77 76 69 S125 77 154 58 S205 62 232 48 S279 53 309 37 S359 41 390 28 S423 26 440 19" />
          </svg>
          <div className="console-metrics">
            <article><CloudRain size={17}/><div><span>7D RAINFALL</span><strong>74.5 <small>mm</small></strong></div></article>
            <article><Waves size={17}/><div><span>RESERVOIR</span><strong>459.04 <small>m</small></strong></div></article>
            <article><Activity size={17}/><div><span>ACTIVE ALERTS</span><strong>00</strong></div></article>
          </div>
          <footer><span>Latest context verified</span><span>Evidence chain complete</span></footer>
        </aside>

        <div className="hero-proof" aria-label="HydroSafe calibration scope">
          <article><strong>96,380</strong><span>historical readings</span></article>
          <article><strong>537</strong><span>instrument profiles</span></article>
          <article><strong>03</strong><span>priority structures</span></article>
          <article><strong>01</strong><span>traceable decision</span></article>
        </div>
      </section>

      <section className="statement-section" id="about" data-reveal>
        <div className="section-index">02 / WHY IT MATTERS</div>
        <div className="statement-copy">
          <span className="eyebrow">The gap between data and decision</span>
          <h2>One high reading is a number. Connected evidence is a decision.</h2>
          <p>A rising reservoir may be expected. Rising pore pressure may follow it. HydroSafe looks across time, weather, water and nearby instruments before presenting the pattern—giving engineers context instead of another isolated chart.</p>
        </div>
        <div className="evidence-chain" aria-label="Example evidence chain">
          <span className="chain-label">A single synchronized view</span>
          <article><CloudRain /><div><small>CONTEXT</small><strong>Rainfall increased</strong></div><span>01</span></article>
          <article><Waves /><div><small>LOAD</small><strong>Reservoir responded</strong></div><span>02</span></article>
          <article><Activity /><div><small>STRUCTURE</small><strong>Piezometer changed</strong></div><span>03</span></article>
          <article className="chain-result"><ShieldCheck /><div><small>INTERPRETATION</small><strong>Within historical response</strong></div><span>04</span></article>
        </div>
      </section>

      <section className="features-section" id="features" data-reveal>
        <div className="section-index">03 / INTELLIGENCE LAYERS</div>
        <header className="section-title"><span className="eyebrow">Five agents, one operational answer</span><h2>Each layer earns its place in the final decision.</h2><p>No black-box verdict. Open any factor and follow the evidence back to its source.</p></header>
        <div className="feature-grid">
          {features.map(({ icon: Icon, ...feature }) => (
            <article key={feature.number} className={feature.className || ""}>
              <div className="feature-top"><span>{feature.number}</span><Icon aria-hidden="true" /></div>
              <div><h3>{feature.title}</h3><p>{feature.text}</p></div>
              <small>{feature.owner}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="workflow-section" id="workflow" data-reveal>
        <div className="section-index">04 / FROM READING TO RESPONSE</div>
        <header className="section-title"><span className="eyebrow">Built for the monitoring shift</span><h2>A clear route from incoming data to human judgment.</h2></header>
        <div className="workflow-line">
          {workflow.map(({ number, icon: Icon, title, text }) => (
            <article key={number}><div className="workflow-icon"><Icon aria-hidden="true" /></div><b>{number}</b><div><h3>{title}</h3><p>{text}</p></div></article>
          ))}
        </div>
      </section>

      <section className="states-section" id="safety" data-reveal>
        <div className="section-index">05 / SAFETY STATES</div>
        <div className="states-copy"><span className="eyebrow">Readable when attention is limited</span><h2>Four states. One language across the project.</h2><p>Every state keeps the score, strongest factors, active thresholds and recommended verification step together.</p></div>
        <div className="state-scale">
          <article className="normal"><span>00—29</span><div className="state-symbol"><CheckCircle2 /></div><h3>NORMAL</h3><p>Continue the approved monitoring schedule.</p></article>
          <article className="watch"><span>30—49</span><div className="state-symbol"><Activity /></div><h3>WATCH</h3><p>Validate the signal and increase review frequency.</p></article>
          <article className="warning"><span>50—69</span><div className="state-symbol"><BellRing /></div><h3>WARNING</h3><p>Begin prompt engineering review and field verification.</p></article>
          <article className="critical"><span>70—100</span><div className="state-symbol"><ShieldCheck /></div><h3>CRITICAL</h3><p>Follow the approved escalation procedure immediately.</p></article>
        </div>
        <p className="safety-note"><ShieldCheck size={15}/> HydroSafe supports—not replaces—authorized engineering judgment and emergency procedures.</p>
      </section>

      <section className="landing-cta" data-reveal>
        <div className="cta-orbit" aria-hidden="true"><span/><span/><span/></div>
        <span className="eyebrow">The full picture is one click away</span>
        <h2>See every signal. Follow every reason. Act with context.</h2>
        <p>Enter the demonstration command center and move through normal, watch, warning and critical scenarios.</p>
        <Link className="button button-primary button-arrow" to={user ? "/dashboard" : "/login"}>{user ? "Enter command center" : "Open demo access"}<ArrowUpRight size={17}/></Link>
      </section>

      <footer className="site-footer"><a href="#home" className="brand"><span>H</span> HydroSafe AI</a><p>Explainable monitoring for safer, faster engineering decisions.</p><a href="#home">Back to top <ArrowUpRight size={14}/></a></footer>
    </main>
  );
}
