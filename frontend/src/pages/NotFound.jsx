import { Link } from "react-router-dom";
import PageMeta from "../components/ui/PageMeta";

export default function NotFound() {
  return (
    <main className="not-found-page">
      <PageMeta title="Page Not Found | HydroSafe AI" description="The requested HydroSafe AI page could not be found." path="/404" />
      <div className="error-code">404</div>
      <div><span className="eyebrow">Signal lost</span><h1>This route is outside the monitored network.</h1><p>The page may have moved, or the address may be incomplete.</p><Link className="button button-primary" to="/">Return home</Link></div>
    </main>
  );
}
