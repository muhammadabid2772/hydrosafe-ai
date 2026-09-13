# Member 2 validation agent

`validation_agent.py` exposes both submitted hydrometeorological validation (`validate_data`) and the structural compatibility entry point required by the orchestrator (`validate_readings`). The original notebook and JSON report are preserved in `original/`.

Structural validation checks completeness, finite numeric values, parseable timestamps and duplicates before Member 3 or Member 6 receives the data. Engineer-approved physical limits remain separate threshold inputs.
