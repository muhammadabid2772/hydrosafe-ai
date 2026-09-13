# Lead Concept vs Risk Agent Scope

## Implemented inside Member 6 Risk Agent

| Lead concept requirement | Implementation |
| --- | --- |
| Threshold warning and alarm | Engineer-sourced upper/lower watch, warning and critical thresholds |
| Alert occurrence record | Deterministic alert ID, time, project, structure, instrument, metric, previous/current values, exceeded limit, direction, severity and source |
| Historical baseline | 537 robust instrument/metric profiles fitted from 96,380 readings |
| Rate of change | Absolute change, percentage change and per-day rate when previous value/timestamp are supplied |
| Historical abnormality | Robust deviation from each instrument's own median and MAD scale |
| Related-condition interpretation | Consumes trend, anomaly and correlation evidence from Members 3–5 |
| Risk and recommendation | Structure-level score, level, leading evidence, deterministic interpretation and review action |
| Sensor status | Per-instrument risk score and level |
| Data quality | Member 2 quality score is a weighted risk factor; missing quality is explicitly marked |
| Hydrometeorological context | Typed, timestamped reservoir, tailwater, inflow/outflow, temperature and rainfall snapshot with freshness and monthly-baseline deviations; zero direct risk contribution |

Application labels map to the lead's wording as follows: `NORMAL` = Normal, `WATCH` = early Warning, `WARNING` = Alarm, and `CRITICAL` = Critical.

## Correctly kept outside Risk Agent

These are necessary for the overall product, but should not be duplicated in Member 6:

- project/structure/instrument navigation and graphs: frontend/dashboard ownership;
- one-day to five-year filtering: trend API and dashboard ownership;
- raw upload, validation and sensor-health checks: Member 2;
- slope, seasonality and rate calculations from full series: Member 3;
- unusual-pattern detection: Member 4;
- reservoir, rainfall, temperature and nearby-sensor response analysis: Member 5. Member 6 normalizes and displays the context, while Member 5 remains responsible for calculating and validating the relationship;
- database persistence and active-alert acknowledgement: lead/orchestration ownership;
- free-form LLM text generation: optional orchestration layer only. The Risk Agent uses a deterministic evidence narrative to avoid unsupported explanations.

## Still required before operational use

- approved project action levels for each selected sensor;
- known incident/maintenance records for outcome-based validation;
- confirmation of sensor units, directionality and active/decommissioned status;
- persistence and acknowledgement workflow for alert events;
- qualified dam-safety engineer review and Emergency Action Plan linkage.
