# Member 6 — Explainable Risk Agent

This folder turns the other agents' outputs into an auditable 0–100 assessment for `ACCRD`, `POWER_HOUSE`, and `POWER_INTAKE`.

It does **not** claim to predict dam failure. The workbooks contain historical observations but no verified incident labels or approved action levels. `train` fits robust per-instrument historical profiles (median, MAD and quantiles). Engineer-approved action levels can be supplied at request time and override a statistical baseline.

The bundled calibration contains 537 profiles fitted from 96,380 readings across 31 selected workbooks. Raw proprietary spreadsheets are intentionally not bundled.

## Contract

`RiskEngine.assess(RiskRequest) -> RiskResponse` accepts current and previous readings, Member 2 quality, Member 3 trends, Member 4 anomalies, Member 5 correlations, optional approved thresholds, and a typed hydrometeorological context snapshot. The response includes the overall level, ranked factors, per-instrument change/rate evidence, deterministic interpretation, threshold alert records, hydromet freshness/monthly deviations, recommended action, model version, and limitations.

The supplied hydrometeorological workbook is useful as external context, not as a labelled failure dataset. Its reviewed daily sheet contains 2,800 dated rows from 2019-01-01 through 2026-09-01. Reservoir level, tailwater level, inflow, temperature and rainfall are substantially complete; outflow begins later. The bundled `hydromet_baseline.json` stores compact monthly robust profiles and the latest contextual snapshot, not the proprietary raw rows. Hydromet contributes zero risk points by itself. Member 5 owns the validated sensor-to-driver comparison and passes that result through `correlations`.

## Local commands

From the repository root after installing `backend/requirements.txt`:

```bash
python -m backend.agents.member6_risk.cli prepare --input /path/to/selected-workbooks --output backend/agents/member6_risk/artifacts/readings.jsonl
python -m backend.agents.member6_risk.cli train --input /path/to/selected-workbooks --output backend/agents/member6_risk/artifacts/baseline.json
python -m backend.agents.member6_risk.cli evaluate --input /path/to/selected-workbooks --output backend/agents/member6_risk/artifacts/evaluation_report.json
python -m backend.agents.member6_risk.cli prepare-hydromet --input /path/to/hydromet.xls --output /tmp/hydromet.jsonl
python -m backend.agents.member6_risk.cli calibrate-hydromet --input /path/to/hydromet.xls --output backend/agents/member6_risk/artifacts/hydromet_baseline.json
python -m backend.agents.member6_risk.cli score --baseline backend/agents/member6_risk/artifacts/baseline.json --hydromet-baseline backend/agents/member6_risk/artifacts/hydromet_baseline.json --request backend/agents/member6_risk/examples/request.json
pytest backend/agents/member6_risk/tests -q
```

## Safety boundary

Risk bands are product display bands, not site-approved action levels. Before operational use, the dam owner and qualified engineer must configure site-specific thresholds, validate formulas and units, back-test known events, define freshness requirements, and connect output to the approved surveillance/Emergency Action Plan. Construction-progress columns, forecasts, dredging comparison tables and short intake-gate studies in the workbook are intentionally excluded from the daily context calibration because they are sparse, duplicated, scenario-specific or require separate engineering interpretation.
