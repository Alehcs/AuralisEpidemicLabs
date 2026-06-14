# Auralis Epidemic Labs

Auralis Epidemic Labs is a socio-cognitive, agent-based simulation workspace
for studying synthetic epidemic outbreaks, information exposure, risk
perception, trust, fatigue, mobility, and policy response.

This repository currently contains **Phase 1: a minimal deterministic ABM
simulation core**. It implements a synthetic SEIR-style model, not a calibrated
real-world disease model.

## Stack

- Frontend: React, TypeScript, Vite
- Backend: Python 3.11+, FastAPI, Pydantic
- Tests: Pytest
- Configuration: JSON today, with a boundary ready for YAML later
- Optional infrastructure: Docker Compose profile for future PostgreSQL work

## Architecture

```text
frontend/         Interactive React client
backend/app/api/  FastAPI delivery adapter
backend/app/application/  Use cases and orchestration
backend/app/domain/       Pure domain entities
backend/app/simulation/   Framework-independent simulation engines
backend/app/schemas/      Pydantic API and config contracts
backend/app/infrastructure/ File/config/export adapters
configs/          Declarative scenarios and experiment inputs
outputs/          Generated runs, snapshots, and reports
docs/             Architecture and project notes
```

The core rule is that `backend/app/simulation` and `backend/app/domain` do not
depend on FastAPI, React, PostgreSQL, or presentation concerns. This keeps the
engine suitable for interactive API use and future batch/headless execution.

## Run the Backend

From the repository root on macOS or another Unix-like environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for Swagger UI or request
`http://127.0.0.1:8000/health` directly.

## Run the Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/health`, `/configs`,
`/simulations`, and `/experiments` to the local backend. For a separately
hosted API, copy `frontend/.env.example` to `frontend/.env` and set
`VITE_API_URL`.

## Tests and Build

```bash
cd backend
source .venv/bin/activate
pytest
```

```bash
cd frontend
npm run typecheck
npm run build
```

## Declarative Configs

Example JSON files live under `configs/` and are grouped into scenarios,
diseases, populations, policies, and experiments. The backend `ConfigLoader`
resolves a config by category and file stem, validates it through Pydantic when
a schema is supplied, and rejects paths outside the config root.

The included disease profile is synthetic and not a medical or epidemiological
claim. Generated runtime data should be written beneath `outputs/`.

## Optional Docker Support

Docker is not required for Phase 1. `docker-compose.yml` contains only an
opt-in PostgreSQL service reserved for later persistence work:

```bash
docker compose --profile future-db up -d postgres
```

The backend intentionally has no PostgreSQL driver or database dependency yet.

## Phase 1 Capabilities

Implemented now:

- Validated scenario, disease, population, policy, and experiment configs
- Deterministic seeded population generation and initial outbreak placement
- Zone routes, probabilistic movement, and aggregate local contacts
- Susceptible, exposed, asymptomatic, symptomatic, recovered, and isolated states
- Functional create, step, run, state, and metrics endpoints
- Per-tick and per-zone metrics plus compact visualization snapshots
- React controls, zone cards, S/E/I/R metrics, and epidemic history

Deliberately deferred:

- Socio-cognitive updates, rumor diffusion, memory, and trust networks
- Calibrated epidemiology, demographics, routines, and contact networks
- Real map geometry and advanced charts or animation
- Durable run storage, PostgreSQL repositories, authentication, workers
- Policy effects, experiment execution, replay, and analysis exports

## Suggested Phase 2 / Prompt 3

Add stable home/work schedules and time-of-day movement, explicit contact event
sampling, policy activation hooks, snapshot export/replay, and a first batch
experiment runner. Keep socio-cognitive behavior behind its existing interface
until epidemiological runs and experiment outputs are reproducible.
