import assert from "node:assert/strict";
import { createServer } from "vite";

const server = await createServer({ server: { host: "127.0.0.1", port: 5199, strictPort: true } });

try {
  await server.listen();
  for (const path of ["/", "/login", "/signup", "/dashboard", "/dashboard/monitoring", "/dashboard/anomalies", "/not-a-real-route"]) {
    const response = await fetch(`http://127.0.0.1:5199${path}`);
    const html = await response.text();
    assert.equal(response.status, 200, `${path} should return the SPA shell`);
    assert.match(html, /HydroSafe AI \| Dam Safety Intelligence/);
    assert.match(html, /og-hydrosafe\.jpg/);
  }
  console.log("Route smoke check passed for landing, auth, dashboard, monitoring, anomaly detector and 404 entry paths.");
} finally {
  await server.close();
}
