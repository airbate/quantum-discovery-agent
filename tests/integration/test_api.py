import time

from fastapi.testclient import TestClient

from app.api import app, registry


def test_run_api_exposes_verified_recommendation():
    registry.payloads.clear()
    registry.results.clear()
    payload = {
        "spec": {
            "run_id": "api-run",
            "name": "API test",
            "candidate_source": {
                "dataset_id": "fixture",
                "feature_columns": ["x"],
                "observed_target_column": "yield",
            },
            "batch": {"size": 2, "total_budget": 2},
            "solver": {"max_quantum_width": 8, "shots": 64, "p": 1, "backend": "fallback"},
        },
        "candidates": [
            {"candidate_id": "a", "raw_features": {"x": 0}, "cost": 1},
            {"candidate_id": "b", "raw_features": {"x": 1}, "cost": 1},
            {"candidate_id": "c", "raw_features": {"x": 2}, "cost": 1},
        ],
        "observations": [
            {"candidate_id": "a", "target": 0.2},
            {"candidate_id": "b", "target": 0.8},
        ],
    }
    client = TestClient(app)
    created = client.post("/api/v1/runs", json=payload)
    assert created.status_code == 201
    executed = client.post("/api/v1/runs/api-run/execute")
    assert executed.status_code == 200
    body = executed.json()
    assert body["status"] == "verified"
    assert body["verification"]["is_feasible"] is True
    assert body["recommendations"]
    assert len(body["agent_events"]) >= 5
    assert body["recommendations"][0]["resource_usage"]["fallback"] is True
    assert any("manifest.json#" in artifact for artifact in body["verification"]["artifact_ids"])
    imported = client.post(
        "/api/v1/runs/api-run/rounds/round_02/observations",
        json={"observations": [{"candidate_id": "c", "target": 0.9}]},
    )
    assert imported.status_code == 200
    rerun = client.post("/api/v1/runs/api-run/execute?round_id=round_02")
    assert rerun.status_code == 200
    assert rerun.json()["round_id"] == "round_02"

    queued = client.post("/api/v1/runs/api-run/jobs?round_id=round_03")
    assert queued.status_code == 202
    job_id = queued.json()["job_id"]
    for _ in range(50):
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert job["status"] == "completed"
