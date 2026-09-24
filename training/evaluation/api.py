"""Minimal evaluation API routes."""

from __future__ import annotations

import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from training.evaluation.benchmarks.registry import list_benchmarks, register_builtin_benchmarks
from training.evaluation.config import EvaluationConfig
from training.evaluation.errors import EvaluationError
from training.evaluation.runners.runner import run_evaluation

router = APIRouter(prefix="/v1/evaluations", tags=["evaluation"])

_RUNS: dict[str, dict] = {}
_CANCEL: dict[str, threading.Event] = {}


class CreateEvaluationRequest(BaseModel):
    benchmark_id: str
    model_id: str = "development-mock-v1"
    model_provider: str = "development_mock"
    output_dir: str = "training/output/evaluation"
    dry_run: bool = False


class EvaluationRunResponse(BaseModel):
    run_id: str
    status: str
    error: str | None = None


def _worker(run_id: str, config: EvaluationConfig, dry_run: bool) -> None:
    try:
        result = run_evaluation(config, dry_run=dry_run, cancelled=_CANCEL[run_id].is_set)
        _RUNS[run_id]["status"] = result.run.status
    except EvaluationError as exc:
        _RUNS[run_id]["status"] = "failed"
        _RUNS[run_id]["error"] = exc.message


@router.get("/benchmarks")
def get_benchmarks() -> list[dict]:
    register_builtin_benchmarks()
    return [item.model_dump(mode="json") for item in list_benchmarks()]


@router.post("/runs", response_model=EvaluationRunResponse)
def create_run(request: CreateEvaluationRequest) -> EvaluationRunResponse:
    register_builtin_benchmarks()
    config = EvaluationConfig(
        benchmark_id=request.benchmark_id,
        model_id=request.model_id,
        model_provider=request.model_provider,
        output_dir=request.output_dir,
    )
    run_id = f"eval_{len(_RUNS) + 1}"
    _RUNS[run_id] = {"status": "running"}
    _CANCEL[run_id] = threading.Event()
    thread = threading.Thread(target=_worker, args=(run_id, config, request.dry_run), daemon=True)
    thread.start()
    return EvaluationRunResponse(run_id=run_id, status="running")


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_run(run_id: str) -> EvaluationRunResponse:
    run = _RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return EvaluationRunResponse(
        run_id=run_id, status=run.get("status", "unknown"), error=run.get("error")
    )


@router.post("/runs/{run_id}/cancel", response_model=EvaluationRunResponse)
def cancel_run(run_id: str) -> EvaluationRunResponse:
    run = _RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    event = _CANCEL.get(run_id)
    if event is not None:
        event.set()
    run["status"] = "cancelled"
    return EvaluationRunResponse(run_id=run_id, status="cancelled")
