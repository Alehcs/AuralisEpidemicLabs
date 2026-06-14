# Auralis Epidemic Labs Backend

FastAPI delivery layer and deterministic, framework-independent scheduled ABM.

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests with `pytest`.

Simulation lifecycle endpoints:

- `POST /simulations/create`
- `POST /simulations/{simulation_id}/step`
- `POST /simulations/{simulation_id}/run`
- `GET /simulations/{simulation_id}/state`
- `GET /simulations/{simulation_id}/metrics`
- `POST /simulations/{simulation_id}/export`
- `GET /runs`
- `GET /runs/{run_id}/metadata`
- `GET /runs/{run_id}/snapshots`
- `POST /experiments/run`
- `GET /experiments/{experiment_id}/results`

Simulations are stored in process memory and disappear when the backend stops.
