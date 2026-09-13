# Member 1 orchestration and reporting

Own the pipeline order and return one payload that validates against `contracts/unified-analysis.schema.json`. Import other agents through their public functions. Do not copy their logic.

Implemented routes:

- `GET /api/analysis/latest` returns the bundled P01DS1 historical replay.
- `POST /api/analysis/run` validates and analyzes caller-supplied structural readings.

Pipeline order: Member 2 validation → invalid-row exclusion → Member 3 trends → Member 6 risk. Member 4 remains optional contextual evidence through its existing routes.
