# Member 4 to Risk Agent integration

## Verified source

The supplied application uses five inputs: reservoir level, tailwater, inflow, rainfall and temperature. Its decision combines absolute z-scores with an Isolation Forest. A parameter is unusual at an absolute z-score of 3 or greater. A multivariate outlier becomes an anomaly only when the maximum absolute z-score is at least 2. Minimum and maximum values are displayed but do not control the decision.

The supplied Drive CSV and the normalized runtime CSV were reconciled across all 2,800 rows. Dates and all five numeric fields matched exactly after header and date-format normalization.

## Data quality

- Date coverage: 2019-01-01 through 2026-09-01
- Missing date: 2021-10-24
- Complete five-parameter rows: 2,679
- Missing reservoir and tailwater rows: 120 each
- Missing temperature rows: 1
- Missing inflow and rainfall rows: 0

The original calculation uses complete cases for the multivariate model. A substantial reservoir operating-regime change occurs in late 2021, so the global z-score is statistical context rather than a site-approved action level.

## Safety boundary

Member 4 results are tagged `HYDROMET`. The Risk Agent records them in `hydromet_assessment` and excludes them from the structural anomaly factor. Structural risk can still increase through instrument baselines, approved thresholds, structural anomalies, trends and Member 5 correlation evidence.

Gemini text from the standalone application is not used as a numerical input. The integrated route remains deterministic and works without a Gemini API key.

## Compatibility

The original Streamlit files remain under `backend/agents/member4_anomaly/original`. FastAPI never imports the Streamlit application. Existing Risk Agent requests do not need new fields because `SignalInput.scope` defaults to `STRUCTURAL`.
