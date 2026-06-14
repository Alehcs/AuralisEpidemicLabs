# Auralis Epidemic Labs - Living Context

Last updated: 2026-06-14

## Purpose

Read this file before planning or implementing changes. Update it whenever work
changes architecture, capabilities, public contracts, important decisions,
commands, configuration, limitations, or the recommended next step. Keep it
concise; code and tests remain the final source of truth.

## Project Goal

Auralis Epidemic Labs is a socio-cognitive agent-based simulation platform for
synthetic epidemic outbreaks, mobility, information exposure, risk perception,
trust, fatigue, and policy response. It supports interactive and headless use.
Configurations are research inputs, not medical guidance or calibrated disease
representations.

## Current Phase

Phase 2 is implemented: Scheduled Mobility, Contacts, Export/Replay, and Batch
Experiments.

Currently functional:

- FastAPI backend and React/TypeScript/Vite frontend.
- Validated JSON scenario, disease, population, policy, and experiment configs.
- Deterministic seeded population and outbreak creation.
- Stable home, work, and optional school assignment across seven routine types.
- Simulation clock with day, hour, minute, and time-of-day labels.
- Schedule-based movement over directed routes; isolated agents never move.
- Minimal susceptible/exposed/asymptomatic/symptomatic/recovered/isolated cycle.
- O(n) zone contact aggregation with retained per-tick contact records.
- Global and per-zone metrics, compact agent samples, and snapshot history.
- In-memory create, step, run, state, and metrics API flow.
- Scheduled policy hooks with deliberately neutral Phase 2 effects.
- Deterministic local run export and compact replay loading.
- Headless batch policy-variant comparison and report generation.
- Frontend clock, contact counts, export button, and experiment result table.

## Architectural Rules

- `backend/app/domain/` and `backend/app/simulation/` are framework-independent.
- Domain/simulation code must not depend on FastAPI, React, PostgreSQL, or UI.
- `application/` coordinates use cases; `api/` adapts HTTP; `schemas/` owns
  Pydantic contracts; `infrastructure/` owns files/config/export adapters.
- Live simulations remain in process memory.
- Exported artifacts live under `outputs/` and are not database persistence.
- Every engine owns a private `random.Random`; identical config and seed must
  produce identical assignments, movement, contacts, and snapshots.
- Policy hooks exist at stable lifecycle points, but effects must remain neutral
  until explicitly designed and tested.

## Simulation Tick

1. Run active policy `before_mobility` hook.
2. Move agents toward schedule destinations.
3. Progress existing exposed/infected agents.
4. Run `before_contacts`; aggregate zone contacts.
5. Run `before_transmission`; apply stochastic local transmission.
6. Compute metrics; run `after_metrics`.
7. Build and retain a compact snapshot.

Transmission uses `beta_base`, effective contacts per day, tick duration,
infectious prevalence, and bounded local density. Pairwise matrices are avoided.

## Important Contracts

Simulation and replay endpoints:

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

Snapshot fields include `simulation_id`, `tick`, fractional `day`, structured
`time`, `agents_summary`, `zone_summary`, `contact_summary`, `active_policies`,
`metrics`, and `sample_agents_for_visualization`.

Run export files:

- `metadata.json`
- `config_summary.json`
- `metrics_history.json`
- `snapshots.jsonl`
- `final_summary.json`

Experiment report files:

- `experiment_summary.json`
- `variant_results.json`
- `run_index.json`

## Primary Configs

- `configs/scenarios/district_v1_market_outbreak.json`
- `configs/diseases/respiratory_like_v1.json`
- `configs/populations/default_population_v1.json`
- `configs/policies/local_alert_policy.json`
- `configs/experiments/global_vs_local_alert.json`

Defaults: 5,000 agents, frontend seed 42, 60-minute ticks, seven routine types,
and a local alert scheduled from tick 24. Policy variants currently produce the
same epidemiological effects because hooks are intentionally neutral.

## Verification Baseline

Last verified on 2026-06-14:

- Backend: `18 passed` with Pytest.
- Frontend TypeScript and production build: passed with Vite 8.0.16.
- `npm audit`: 0 vulnerabilities.
- Browser integration: create, run 24 ticks, schedule time/contact update,
  export, batch experiment, and experiment table completed without console errors.
- Replay integration: exported run metadata and 25 snapshots for ticks 0-24
  loaded successfully; stored experiment results returned two variants.

```bash
cd backend
source .venv/bin/activate
pytest
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
npm run typecheck
npm run build
npm audit
npm run dev
```

## Intentional Placeholders

- Cognitive decisions, trust, fatigue, memory, and behavior adaptation.
- Information and rumor propagation.
- Real policy effects, isolation incentives, closures, and alerts.
- Pair-level contact networks and advanced replay UI.
- PostgreSQL, authentication, workers, WebSockets, and LLMs.
- Real district geometry, advanced visualization, and animation.

## Recommended Next Step

Phase 3 / Prompt 4 should implement real alert/closure/isolation effects,
richer experiment comparison/export, and a minimal information exposure event
model without yet implementing full cognition or rumor propagation.

## Update Protocol

After meaningful work:

1. Update `Last updated`.
2. Revise phase and functional capabilities.
3. Record architectural decisions future work must preserve.
4. Update API, snapshot, config, and file contracts.
5. Record only verification commands actually executed.
6. Remove completed placeholders and add real limitations.
7. Keep the recommended next step aligned with project state.

Do not record transient process IDs, generated run IDs, debugging notes, or
unaccepted speculation.
