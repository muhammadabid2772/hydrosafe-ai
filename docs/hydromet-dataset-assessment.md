# Hydrometeorological Dataset Assessment

## Decision

Use the workbook for environmental and operating context. Do not use it as a labelled dam-failure target or let it independently trigger structural alarms.

The canonical source for calibration is the `2021~2026` sheet because it contains the full daily series. The `2019~2020` sheet duplicates the early period and is therefore excluded to prevent double counting.

## Reviewed daily data

| Field | Coverage | Use |
| --- | ---: | --- |
| Date | 2,800 / 2,800 | Daily join key |
| Reservoir level | 95.7% | External hydraulic load context |
| Tailwater level | 95.7% | Power House/outlet operating context |
| Inflow | 100.0% | Catchment/operating context |
| Outflow | 34.9% | Context only when present; do not impute the early period |
| Mean temperature | 100.0% except one value | Seasonal/thermal response context |
| Daily rainfall | 100.0% | Rainfall and rolling-rain context |

Date range: 2019-01-01 through 2026-09-01. The only missing daily date is 2021-10-24. The final row has a missing temperature value. No values are silently filled.

## Intentionally excluded from calibration

| Workbook content | Reason |
| --- | --- |
| Dam-fill and asphalt-core construction elevations | Construction history, sparse and not a continuous operating driver |
| Dredging/tailwater comparison sheets | Special-study tables with duplicated observations and changed operating conditions |
| 2025 forecast | Scenario/forecast values must not be mixed with observations |
| 2025/2026 unit-operation measurements | Useful for a dedicated hydraulic performance model, but too sparse and task-specific for the daily context baseline |
| Intake gate water-level study | Short-duration engineering study; preserve for a separate Power Intake analysis |
| Settlement, horizontal displacement and crack summary columns | Sparse structural outcomes that duplicate instrument-domain data and lack verified event labels |

## Implemented pipeline

- `prepare-hydromet` writes a normalized, one-row-per-day JSONL file when an analyst needs it.
- `calibrate-hydromet` builds month-specific median/MAD/quantile profiles and a latest snapshot.
- `RiskRequest.hydromet` accepts a typed current snapshot.
- `RiskResponse.hydromet_assessment` reports freshness and monthly standardized deviations.
- Direct hydromet risk contribution is fixed at zero. Member 5 must validate a sensor-versus-driver relationship and supply it through `correlations` before it affects the Risk Agent score.

## Operational limitations

The workbook contains no verified incident labels, approved action levels, provenance for individual values, or documented uncertainty. Before operational use, confirm timestamps/time zone, measurement units, reservoir/tailwater datum, rainfall station identity, revisions, and approved freshness requirements with the project engineer.
