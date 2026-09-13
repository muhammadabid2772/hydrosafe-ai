import { useAuth } from "../../contexts/AuthContext";
import { NavLink } from "react-router-dom";
import { USE_MOCK_ANALYSIS } from "../../services/api";

const Icon = ({ name }) => {
  const paths = {
    overview: <><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" /></>,
    monitoring: <><path d="M3 12h4l2-5 4 10 2-5h6" /></>,
    anomaly: <><path d="M12 3 2.8 20h18.4L12 3Z" /><path d="M12 9v4m0 3h.01" /></>,
    correlation: <><circle cx="6" cy="7" r="3" /><circle cx="18" cy="17" r="3" /><path d="m8.5 9 7 6" /></>,
    reports: <><path d="M6 3h9l4 4v14H6z" /><path d="M15 3v5h5M9 13h6m-6 4h6" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1A8 8 0 0 0 15 6l-.3-2.6h-4L10.5 6A8 8 0 0 0 9 7.1l-2.4-1-2 3.4 2 1.5a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.4-1A8 8 0 0 0 10.5 18l.3 2.6h4L15 18a8 8 0 0 0 1.5-1.1l2.4 1 2-3.4-2-1.5a7 7 0 0 0 .1-1Z" /></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>;
};

const items = [
  { id: "overview", label: "Risk overview", to: "/dashboard", end: true },
  { id: "monitoring", label: "Monitoring trends", to: "/dashboard/monitoring" },
  { id: "anomaly", label: "Anomaly detector", to: "/dashboard/anomalies" },
  { id: "correlation", label: "Correlations", to: "/dashboard/correlations" },
  { id: "reports", label: "Reports", to: "/dashboard/reports" },
];

export default function DashboardSidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="dashboard-sidebar">
      <a href="/" className="sidebar-brand" aria-label="HydroSafe AI home"><span>H</span><b>HydroSafe</b></a>
      <div className="sidebar-project"><small>{USE_MOCK_ANALYSIS ? "DEMO PROJECT" : "CONNECTED PROJECT"}</small><strong>Demo Dam 01</strong><span><i /> {USE_MOCK_ANALYSIS ? "Simulated scenarios" : "Unified API connected"}</span></div>
      <nav aria-label="Dashboard sections">
        {items.map((item) => item.to ? (
          <NavLink key={item.id} to={item.to} end={item.end} className={({ isActive }) => isActive ? "active" : ""}>
            <Icon name={item.id} /><span>{item.label}</span>
          </NavLink>
        ) : (
          <button key={item.id} disabled title={`${item.label} is not available in this prototype`}>
            <Icon name={item.id} /><span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <NavLink to="/dashboard/settings"><Icon name="settings" /><span>Settings</span></NavLink>
        <div className="operator-row"><span>{(user?.name || user?.email || "OP").slice(0, 2).toUpperCase()}</span><div><strong>{user?.name || "Operator"}</strong><small>{user?.email}</small></div></div>
        <button className="sidebar-logout" onClick={logout}>Log out</button>
      </div>
    </aside>
  );
}
