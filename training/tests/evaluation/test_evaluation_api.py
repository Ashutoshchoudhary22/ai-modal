from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_evaluation_api_dry_run():
    from training.evaluation.api import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    benchmarks = client.get("/v1/evaluations/benchmarks")
    assert benchmarks.status_code == 200
    assert any(item["benchmark_id"] == "coding-mini" for item in benchmarks.json())

    create = client.post(
        "/v1/evaluations/runs",
        json={"benchmark_id": "coding-mini", "dry_run": True},
    )
    assert create.status_code == 200
    run_id = create.json()["run_id"]
    status = client.get(f"/v1/evaluations/runs/{run_id}")
    assert status.status_code == 200
