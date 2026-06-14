"""Simulation API lifecycle integration tests."""

import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_create_step_run_state_and_metrics_flow() -> None:
    async def exercise_flow() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            created = await client.post(
                "/simulations/create",
                json={
                    "scenario_config": "district_v1_market_outbreak",
                    "disease_config": "respiratory_like_v1",
                    "population_config": "default_population_v1",
                    "policy_config": "local_alert_policy",
                    "seed": 123,
                },
            )
            assert created.status_code == 201
            simulation_id = created.json()["simulation_id"]
            assert created.json()["snapshot"]["tick"] == 0

            stepped = await client.post(f"/simulations/{simulation_id}/step")
            assert stepped.status_code == 200
            assert stepped.json()["snapshot"]["tick"] == 1

            ran = await client.post(
                f"/simulations/{simulation_id}/run",
                json={"ticks": 3},
            )
            assert ran.status_code == 200
            assert ran.json()["snapshot"]["tick"] == 4

            state = await client.get(f"/simulations/{simulation_id}/state")
            assert state.status_code == 200
            assert state.json()["snapshot"]["tick"] == 4

            metrics = await client.get(f"/simulations/{simulation_id}/metrics")
            assert metrics.status_code == 200
            assert len(metrics.json()["history"]) == 5

            missing = await client.get("/simulations/unknown/state")
            assert missing.status_code == 404

            missing_config = await client.post(
                "/simulations/create",
                json={"scenario_config": "does_not_exist"},
            )
            assert missing_config.status_code == 404
            assert "Config not found" in missing_config.json()["detail"]

    asyncio.run(exercise_flow())
