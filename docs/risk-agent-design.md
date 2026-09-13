# Risk Agent Design and Validation Note

## Scope

The delivered calibration covers three structure groups only:

- ACCRD — asphalt concrete core rockfill dam;
- Power House — files under `PH`, including GPH instrument IDs;
- Power Intake — files under `PI`, including PIT instrument IDs.

The extractor deliberately ignores report/chart sheets and reads supported instrument-level histories. It detects bilingual observation-date headers and caps scanned columns to avoid Excel formatting artifacts extending to column 16,384.

## Why this is a hybrid risk layer

The archive has measurements and descriptive summaries, but the label audit found no verified incident classes and no approved action-level table. A supervised model trained on invented labels would produce misleading accuracy. The implementation instead uses:

1. per-instrument median, MAD, robust scale and quantiles fitted from history;
2. current-reading deviation from the matching profile;
3. validated scores from the quality, trend, anomaly and correlation agents;
4. optional engineer-approved upper/lower thresholds, each requiring a source;
5. an explicit weighted fusion and strongest-factor contribution;
6. evidence, limitations and mandatory human review in every response.

Display bands are `NORMAL < 30`, `WATCH 30–49.99`, `WARNING 50–69.99`, and `CRITICAL >= 70`. These are application bands—not project action levels.

## Technical basis

The architecture follows the monitoring principles in the U.S. Bureau of Reclamation's *Design Standards No. 13, Chapter 11: Instrumentation and Monitoring*, which covers monitoring-program design, evaluation of monitoring information, and response to unusual observations. FERC's Chapter 14 guidance frames the Dam Safety Performance Monitoring Program around project-specific procedures and criteria. These sources support evidence fusion and escalation workflows; they do not supply universal numeric thresholds for this project.

- USBR design standards index: https://www.usbr.gov/tsc/techreferences/designstandards-datacollectionguides/designstandards.html
- FERC Chapter 14 page: https://www.ferc.gov/dam-safety-performance-monitoring-program-dspmp-engineering-guidelines
- Official USACE publications repository: https://www.publications.usace.army.mil/

## Validation completed

- 31 selected workbooks (120,467,816 bytes) profiled;
- 96,380 historical readings retained in 537 instrument/metric profiles: ACCRD 299, Power House 181, Power Intake 57;
- BM, BV, CZ, D, E, GB, ID, IN, J, M, P, R, S, TC, TP and WE families represented where present in the three-structure scope;
- chronological 80/20 stability evaluation, with profiles fitted only on earlier readings;
- deterministic synthetic robust-z escalation check;
- unit tests for clean evidence, missing upstream quality, and monotonic anomaly severity;
- FastAPI schema validation and health/risk route smoke tests;
- frontend contract and production-build tests.

Because no truth labels exist, the report never calls holdout deviations “accuracy,” “precision,” or “false positives.” Operational validation still requires known-event records, approved thresholds, instrument status/decommission logs, unit verification, and sign-off by the responsible dam-safety engineer.
