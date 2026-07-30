# InsignIA API (FastAPI)

API backend scaffold for InsignIA.

Run locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Configure PostgreSQL connection in `.env` (see `.env.example`).
