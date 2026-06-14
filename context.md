# Auralis Epidemic Labs - Living Context

Last updated: 2026-06-14

## Purpose

Read this file before planning or implementing changes. Update it whenever work
changes architecture, capabilities, public contracts, important decisions,
commands, configuration, limitations, or the recommended next step. Code and
tests remain the final source of truth.

## Project Goal

Auralis Epidemic Labs is a deterministic socio-cognitive agent-based simulation
platform for synthetic epidemic outbreaks, mobility, information exposure,
risk perception, trust, fatigue, and policy response. Configurations are
research inputs, not medical guidance or calibrated disease representations.

## Current Phase

Phase 3 is implemented: Real Policy Effects and Minimal Official Information
Exposure.

Currently functional:

- FastAPI backend and React/TypeScript/Vite frontend.
- Deterministic seeded population, schedules, movement, contacts, and SEIR cycle.
- Multiple scheduled policies per simulation with backward-compatible single-policy input.
- `local_alert`, `global_alert`, `zone_closure`, and `isolation_encouragement` policy types.
- Bounded agent alert exposure, perceived risk, policy memory, and seeded compliance traits.
- Optional movement reduction, target-zone avoidance, contact reduction, and transmission modifiers.
- Symptomatic isolation with strongly reduced contacts and continued clinical recovery.
- Policy reach, mean risk/exposure, isolation, contacts, and reduction metrics in history/snapshots.
- Local run export/replay and four-arm deterministic batch comparison.
- Frontend policy list, risk/exposure metrics, isolated count, reduction estimates, zone badges, and batch table.

## Architectural Rules

- `backend/app/domain/` and `backend/app/simulation/` are framework-independent.
- Domain/simulation code must not depend on FastAPI, React, PostgreSQL, or UI.
- `application/` coordinates use cases; `api/` adapts HTTP; `schemas/` owns
  Pydantic contracts; `infrastructure/` owns files/config/export adapters.
- Live simulations remain in process memory; exports under `outputs/` are not persistence.
- Every engine owns a private `random.Random`; identical config and seed must produce identical snapshots.
- Policy effects are bounded multipliers resolved by `PolicyHookEngine` and consumed by independent engines.
- Official alerts are modeled by `InformationEngine`; rumor propagation remains absent.

## Simulation Tick

1. Resolve active policies and intervention multipliers.
2. Apply official-alert exposure and perceived-risk updates.
3. Progress disease and apply deterministic symptomatic isolation.
4. Move agents, reducing optional movement and avoiding closed targets.
5. Aggregate zone contacts with policy and isolation multipliers.
6. Apply local stochastic transmission with contact/transmission multipliers.
7. Compute metrics, run the final policy hook, and retain a compact snapshot.

Transmission remains an aggregate zone hazard using `beta_base`, tick duration,
contact rate, local density, infectious prevalence, and policy multipliers.
Pairwise contact matrices are intentionally avoided.

## Important Contracts

Simulation endpoints:

- `POST /simulations/create`
- `POST /simulations/{simulation_id}/step`
- `POST /simulations/{simulation_id}/run`
- `GET /simulations/{simulation_id}/state`
- `GET /simulations/{simulation_id}/metrics`
- `GET /simulations/{simulation_id}/policies`
- `POST /simulations/{simulation_id}/export`
- `GET /runs`
- `GET /runs/{run_id}/metadata`
- `GET /runs/{run_id}/snapshots`
- `POST /experiments/run`
- `GET /experiments/{experiment_id}/results`

`SimulationCreateRequest` accepts legacy `policy_config` or `policy_configs`.
Snapshots include active policy IDs, per-zone policy IDs, policy effect summary,
alert/risk metrics, contact summaries, and sampled agent exposure/compliance.

## Primary Configs

- `configs/policies/local_alert_policy.json`
- `configs/policies/global_alert_policy.json`
- `configs/policies/isolation_encouragement_policy.json`
- `configs/policies/market_zone_closure_policy.json`
- `configs/experiments/global_vs_local_alert.json`

The batch experiment variants are `baseline_no_policy`, `global_alert`,
`local_alert_market`, and `local_alert_plus_isolation`, sharing seeds.

## Verification Status

Executed on 2026-06-14:

- `python3 -m compileall -q app tests`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed with Vite 8.0.16.
- `git diff --check`: passed.

Not completed in this session because sandbox escalation was rejected after the
environment reached its approval/usage limit:

- Backend dependency installation and `pytest`.
- Registry-backed `npm audit` (the sandbox DNS request failed first).
- Local browser verification (binding port 5173 was denied).

Run when the environment permits:

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest
```

```bash
cd frontend
npm run typecheck
npm run build
npm audit
npm run dev
```

## Intentional Placeholders

- Adaptive trust, fatigue, cognitive decisions, and behavior change.
- Rumor creation, diffusion, source credibility, and social networks.
- Calibrated epidemiology, demographics, and pair-level contacts.
- PostgreSQL, authentication, workers, WebSockets, and LLMs.
- Real district geometry, advanced animation, and replay controls.

## Recommended Next Step

Phase 4 should implement adaptive cognition and competing information: trust and
fatigue updates, policy-memory decay, compliance response, and official versus
rumor events. Keep all updates deterministic and policy/config driven.

## Update Protocol

After meaningful work, revise the phase, contracts, verification facts,
placeholders, and recommended next step. Do not record transient process IDs,
generated run IDs, debugging notes, or speculation.
