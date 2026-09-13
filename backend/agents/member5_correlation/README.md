# Member 5 — Hydro-Structural Correlation Engine

Member 5 is implemented as an evidence engine rather than a fabricated predictive model. The updated repository does not contain a labelled, time-aligned hydro-structural failure dataset, so training a classifier would create false confidence.

The engine now provides two auditable paths:

1. Exact-timestamp Pearson co-movement for structural series with at least four matched observations. Detection requires `|r| >= 0.70` and is explicitly labelled association, not causation.
2. Cross-signal temporal reasoning when Member 4 provides elevated hydrometeorological anomaly context and Member 3 or Member 4 structural evidence is also elevated.

Detected evidence is converted to the shared `SignalInput` contract and passed directly into Member 6's correlation factor. The unified API also returns the complete Member 5 evidence list for the frontend correlation workspace.
