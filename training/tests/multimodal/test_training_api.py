from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_multimodal_training_api_dry_run(tmp_path: Path):
    pytest.importorskip("torch")
    from training.multimodal.api import router

    config_path = Path("training/configs/multimodal/sft.yaml").resolve()
    config = config_path.read_text(encoding="utf-8")
    override = tmp_path / "api-smoke.yaml"
    override.write_text(
        config.replace("training/output/multimodal-mini-sft", str(tmp_path / "out")),
        encoding="utf-8",
    )

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    create = client.post(
        "/v1/training/multimodal/runs", json={"config_path": str(override), "dry_run": True}
    )
    assert create.status_code == 200
    run_id = create.json()["run_id"]

    import time

    for _ in range(50):
        status = client.get(f"/v1/training/multimodal/runs/{run_id}")
        if status.json()["status"] in {"validated", "completed", "failed"}:
            break
        time.sleep(0.1)
    assert status.status_code == 200

    cancel = client.post(f"/v1/training/multimodal/runs/{run_id}/cancel")
    assert cancel.status_code == 200
