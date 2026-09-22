# AlgoControl Research & Validation Terminal

Safe proof of concept for José Bordas. The project compares deterministic mock market data with synthetic data across demonstration algorithms, risk metrics and stress scenarios.

## Safety boundary

This demo has no broker connection, no order endpoint and no order execution. The frontend explicitly labels `MOCK`, `SYNTHETIC`, `PAPER` and `SHADOW` modes. `MOCK` is not a real market feed.

The existing Streamlit validation app remains intact. The José-facing proof of concept is the new FastAPI + vanilla HTML frontend.

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the read-only API:

```bash
python -m uvicorn backend.main:app --reload
```

In another terminal, serve the frontend:

```bash
python -m http.server 8080 --directory frontend
```

Open http://localhost:8080. The API must be running on http://localhost:8000.

Run tests:

```bash
pytest
```

## Architecture

- `backend/providers.py`: deterministic mock and synthetic providers.
- `backend/algorithms.py`: four demonstration algorithms with one common interface.
- `backend/evaluation.py`: shared metrics and transfer divergence.
- `backend/main.py`: read-only FastAPI endpoints; deliberately no order endpoint.
- `backend/storage.py`: SQLite audit store.
- `frontend/`: index.html-style AlgoControl terminal with dark/light themes, comparison, synthetic quality, scenarios and audit.
- `app.py`: original Streamlit application preserved for internal validation.

## What is implemented

- mock versus synthetic market data;
- algorithm comparison;
- risk metrics;
- synthetic-quality components;
- scenario lab using the existing scenario generator;
- paper/shadow safety labels;
- audit records;
- polling every 15 seconds;
- responsive dark/light frontend.

## Not implemented

- real market provider;
- broker integration;
- live orders;
- authentication;
- WebSockets;
- production database migration.

These are intentionally excluded from the proof of concept.
