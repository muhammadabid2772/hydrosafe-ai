# Backend integration shell

`backend.main` now provides a minimal FastAPI service with `/health` and Member 6's `/api/risk/assess` route. Other members can add routers without changing the risk-agent package. Authentication persistence remains a lead-owned integration task.

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Interactive API documentation is at `http://127.0.0.1:8000/docs`.
