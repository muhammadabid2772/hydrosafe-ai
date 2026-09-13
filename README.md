# HydroSafe AI — Integrated Six-Agent Hackathon MVP

HydroSafe AI is an agentic hydrological and dam-safety monitoring MVP. The updated build connects the complete evidence path required by the hackathon plan: data validation, trend intelligence, anomaly screening, hydro-structural correlation, dynamic risk/early warning, and explainable reporting.

## What is now implemented

The primary pipeline is:

`Member 2 validation → Member 3 trends → Member 4 anomaly screening → Member 5 correlation → Member 6 risk/warning → grounded report`

Member 4 now has two roles. The original five-parameter hydrometeorological screen remains preserved and contextual, while a new structural anomaly screen automatically evaluates validated structural series using robust deviation, rolling deviation, and Isolation Forest when enough history exists.

Member 5 is implemented from scratch as an auditable evidence engine. The supplied files do not contain a labelled, time-aligned hydro-structural failure dataset, so the project does not pretend to train a failure classifier. Instead it uses exact-timestamp Pearson co-movement plus deterministic cross-signal reasoning between elevated hydromet evidence and structural trends/anomalies.

Member 6 consumes real evidence from Members 2–5, keeps the 0–100 risk bands, produces warnings and recommended actions, and now works with real authentication, account settings, persisted reports, and a complete dashboard route set.

## Backend setup

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Copy the backend environment template and fill only your own secrets:

```bash
cp backend/.env.example backend/.env
```

Important variables:

```env
CORS_ORIGINS=http://localhost:5173
AUTH_SECRET=replace-with-a-long-random-secret
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Do not commit the real API key. The supplied key is intentionally not embedded in the source archive.

Start the API:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The real backend is the default configuration:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=false
VITE_USE_MOCK_ANALYSIS=false
```

Create an account from `/signup`, then use the dashboard.

## Dashboard routes

- `/dashboard` — dynamic risk overview and warning evidence
- `/dashboard/monitoring` — Member 2 data quality + Member 3 structural trends
- `/dashboard/anomalies` — Member 4 hydromet screening, with latest ACCRD structural evidence reused when available
- `/dashboard/correlations` — Member 5 correlation evidence and confidence
- `/dashboard/reports` — generate, save, review and download engineering reports
- `/dashboard/settings` — update operator profile and password

## Report generation

Reports are grounded in the exact unified analysis snapshot. A deterministic report is always generated first. If `OPENROUTER_API_KEY` exists, OpenRouter is used only to improve the wording and organization under a strict prompt that forbids invented measurements, causes, thresholds or failure probabilities. If the API is unavailable, the deterministic report is saved instead.

## Persistence

HydroSafe uses SQLAlchemy. Local development defaults to `backend/database/hydrosafe.db`. For Railway, attach PostgreSQL and provide `DATABASE_URL`; the backend automatically switches to PostgreSQL through `psycopg`.

For SQLite on Railway, use a persistent Railway volume and set `HYDROSAFE_DB_PATH` to a path on that volume. PostgreSQL is the preferred deployment option for accounts and report history.

## Main APIs

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/settings/profile`
- `PUT /api/settings/password`
- `GET /api/analysis/latest`
- `POST /api/analysis/run`
- `POST /api/anomaly/hydromet/assess`
- `POST /api/correlation/analyze`
- `POST /api/risk/assess`
- `POST /api/risk/assess-with-member4`
- `POST /api/reports/generate`
- `GET /api/reports`

See `contracts/api-contract.md` for payload details.

## Verification

Backend verification command:

```bash
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm test
npm run test:routes
npm run build
```

The current integration tests cover validation, trends, hydromet and structural anomaly logic, correlation evidence, risk propagation, authentication, password changes, unified analysis, and report persistence.

## Deployment to Railway

The repository already contains `railway.toml` and `Procfile`. Railway starts:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

For deployment set at minimum:

- `AUTH_SECRET`
- `CORS_ORIGINS`
- `DATABASE_URL` from an attached Railway PostgreSQL service
- `OPENROUTER_API_KEY` for AI-enhanced report wording
- optionally `OPENROUTER_MODEL`

Do not deploy proprietary raw Excel archives or secret documents.

## Engineering boundary

This is a polished hackathon MVP, not an industrial dam-control system. Statistical anomaly and correlation evidence do not prove structural danger or causation. Product risk bands are not engineer-approved action levels. Operational use requires site-specific thresholds, verified telemetry, field confirmation, qualified engineering review, and the approved Emergency Action Plan.
