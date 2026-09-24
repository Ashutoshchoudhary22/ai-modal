"""Minimal multimodal training API routes."""

from __future__ import annotations

import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode
from training.multimodal.experiment import MultimodalExperimentMetadata
from training.multimodal.trainer import run_multimodal_training

router = APIRouter(prefix="/v1/training/multimodal", tags=["multimodal-training"])

_RUNS: dict[str, dict[str, Any]] = {}
_CANCEL_FLAGS: dict[str, threading.Event] = {}


class CreateRunRequest(BaseModel):
    config_path: str = Field(min_length=1)
    dry_run: bool = False


class RunResponse(BaseModel):
    run_id: str
    status: str
    experiment_id: str | None = None
    checkpoint_path: str | None = None
    error: str | None = None


def _run_worker(run_id: str, config_path: Path, dry_run: bool) -> None:
    cancel_event = _CANCEL_FLAGS[run_id]
    try:
        final_dir = run_multimodal_training(
            config_path,
            dry_run=dry_run,
            cancelled=cancel_event.is_set,
        )
        _RUNS[run_id]["status"] = "completed" if not dry_run else "validated"
        _RUNS[run_id]["checkpoint_path"] = str(final_dir)
    except MultimodalTrainingError as exc:
        _RUNS[run_id]["status"] = (
            "cancelled" if exc.code == MultimodalTrainingErrorCode.TRAINING_CANCELLED else "failed"
        )
        _RUNS[run_id]["error"] = exc.message
        _RUNS[run_id]["error_code"] = str(exc.code)


@router.post("/runs", response_model=RunResponse)
def create_run(request: CreateRunRequest) -> RunResponse:
    config_path = Path(request.config_path)
    if not config_path.exists():
        raise HTTPException(status_code=400, detail="config_path not found")
    if ".." in config_path.parts:
        raise HTTPException(status_code=400, detail="invalid config_path")

    run_id = f"run_{len(_RUNS) + 1}"
    experiment = MultimodalExperimentMetadata(
        experiment_id=run_id,
        run_id=run_id,
        dataset_id="pending",
        dataset_version="pending",
        dataset_fingerprint="pending",
        model_id="pending",
        training_config={},
        seed=0,
        created_at="",
        status="created",
    )
    _RUNS[run_id] = asdict(experiment)
    _RUNS[run_id]["status"] = "running"
    _CANCEL_FLAGS[run_id] = threading.Event()

    thread = threading.Thread(
        target=_run_worker,
        args=(run_id, config_path.resolve(), request.dry_run),
        daemon=True,
    )
    thread.start()
    return RunResponse(run_id=run_id, status="running", experiment_id=run_id)


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str) -> RunResponse:
    run = _RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return RunResponse(
        run_id=run_id,
        status=run.get("status", "unknown"),
        experiment_id=run.get("experiment_id"),
        checkpoint_path=run.get("checkpoint_path"),
        error=run.get("error"),
    )


@router.post("/runs/{run_id}/cancel", response_model=RunResponse)
def cancel_run(run_id: str) -> RunResponse:
    run = _RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    event = _CANCEL_FLAGS.get(run_id)
    if event is not None:
        event.set()
    run["status"] = "cancelled"
    return RunResponse(run_id=run_id, status="cancelled", experiment_id=run.get("experiment_id"))
