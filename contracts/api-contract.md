# HydroSafe AI Integrated MVP Contract

Contract owner: Member 1 lead. The unified analysis endpoint is the primary product contract; individual agent endpoints remain available for focused testing.

## Authentication and settings

### `POST /api/auth/signup`

```json
{ "name": "Operator Name", "email": "operator@example.com", "password": "minimum-eight-characters" }
```

Returns a signed bearer token and user object. Passwords are stored only as PBKDF2-SHA256 hashes with per-user salts.

### `POST /api/auth/login`

Accepts `email` and `password` and returns the same token/user shape as signup.

### `GET /api/auth/me`

Requires `Authorization: Bearer <token>` and returns the authenticated user.

### `POST /api/auth/logout`

Returns `{ "status": "ok" }`. Tokens are stateless and expire after 12 hours.

### `PUT /api/settings/profile`

Updates the authenticated operator display name.

### `PUT /api/settings/password`

```json
{ "current_password": "old-password", "new_password": "new-password" }
```

Verifies the current password and replaces the stored hash.

## Unified analysis

### `GET /api/analysis/latest?project_id=demo-dam-01`

Runs the included ACCRD historical replay through the connected pipeline and returns `data_mode=HISTORICAL_REPLAY`. It must never be described as live telemetry.

### `POST /api/analysis/run`

Runs caller-supplied structural time-series data through:

1. Member 2 validation and sensor-health evidence.
2. Member 3 timestamp-aware trend analysis.
3. Member 4 structural anomaly screening using robust deviation, rolling deviation and Isolation Forest when enough history exists.
4. Member 5 Pearson/temporal cross-signal correlation analysis.
5. Member 6 risk scoring, warning state, ranked factors, approved-threshold alerts and recommended next action.
6. Lead-owned report metadata for the synchronized snapshot.

Invalid rows are excluded and reported. A calculated zero remains numeric `0`; unavailable evidence uses explicit availability/status fields.

## Member 4 anomaly routes

### `POST /api/anomaly/hydromet/assess`

Runs the preserved five-parameter hydrometeorological z-score + Isolation Forest screen against the shared 2,800-row history. Its scope is always `HYDROMET` and it never adds structural risk points by itself.

### `POST /api/risk/assess-with-member4`

Runs a normal `RiskRequest` plus current hydrometeorological values. The frontend ACCRD anomaly workspace first attempts to reuse the latest validated structural evidence so Agent 6 can produce an assessed risk state; if structural evidence is unavailable, the safe `NOT_ASSESSED` boundary remains.

## Member 5 correlation route

### `POST /api/correlation/analyze`

Accepts validated time-series readings plus optional trend/anomaly signals. It returns:

- `correlation_detected`
- confidence and score
- related parameters
- Pearson coefficient and paired-point count when applicable
- concise explanation
- risk-ready `SignalInput` records

Correlation is explicitly association evidence, not causation. No labelled hydro-structural failure dataset is bundled, so the MVP does not fabricate a trained classifier.

## Reports

### `POST /api/reports/generate`

Requires authentication and accepts the synchronized unified analysis payload. The backend first creates a deterministic grounded engineering report. When `OPENROUTER_API_KEY` is configured, the reporting service asks OpenRouter to rewrite that grounded draft while forbidding invented thresholds, measurements, causes or failure probabilities. If the provider is unavailable, deterministic reporting remains functional.

### `GET /api/reports`

Returns the authenticated user's latest saved reports.

## Persistence

The backend uses SQLAlchemy. Local development defaults to SQLite. If `DATABASE_URL` is supplied, Railway/PostgreSQL is supported through `psycopg`.

## Safety boundary

HydroSafe is an engineering decision-support MVP. Statistical anomaly, correlation and risk bands are not site-approved emergency action levels. Qualified dam-safety review and approved site procedures remain mandatory.
