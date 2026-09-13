# Member 4 anomaly agent

This folder preserves Member 4's Streamlit pipeline and provides a separate, import-safe API integration.

## Ownership and compatibility

`original/app.py` and `original/requirements.txt` are the supplied standalone application. The FastAPI backend never imports that Streamlit module, so page-level Streamlit calls cannot affect API startup. Run it independently with:

```bash
python -m pip install -r backend/agents/member4_anomaly/original/requirements.txt
streamlit run backend/agents/member4_anomaly/original/app.py
```

The original app expects these CSV columns:

```text
reservoir_level,tailwater,inflow,rainfall,temperature
```

The reviewed source CSV uses human-readable headers. `core.py` accepts both forms, and `scripts/prepare_member4_hydromet.py` creates a canonical CSV without modifying the original data.

## API contract

`POST /api/anomaly/hydromet/assess` runs Member 4's deterministic z-score plus Isolation Forest screen. `POST /api/risk/assess-with-member4` runs the same screen and passes its typed result into the Risk Agent.

Member 4 signals use `scope=HYDROMET`. They are recorded as context and contribute zero direct points to structural risk. Member 5 supplies any validated hydromet-to-structure relationship through correlation evidence.

Gemini remains part of the standalone Streamlit explanation. The integrated Risk Agent uses only deterministic statistics and a cautious deterministic summary, so Railway does not require a Gemini key.
