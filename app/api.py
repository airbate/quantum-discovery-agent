from __future__ import annotations

import copy
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.agents.orchestrator import AgentOrchestrator
from app.domain.errors import QDiscoveryError
from app.domain.models import Candidate, ExperimentDesignSpec, Observation
from app.modeling.active_learning import append_observations
from app.runtime.artifacts import ArtifactStore
from app.runtime.jobs import JobRunner


class CreateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec: ExperimentDesignSpec
    candidates: list[Candidate] = Field(min_length=1)
    observations: list[Observation] = Field(default_factory=list)


class ObservationImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[Observation] = Field(min_length=1)


class RunRegistry:
    def __init__(self):
        self.payloads: dict[str, CreateRunRequest] = {}
        self.results: dict[str, dict[str, Any]] = {}


registry = RunRegistry()
job_runner = JobRunner()
artifact_store = ArtifactStore("artifacts")
app = FastAPI(title="Q-Discovery Agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "q-discovery-agent"}


@app.post("/api/v1/runs", status_code=201)
def create_run(request: CreateRunRequest) -> dict[str, str]:
    registry.payloads[request.spec.run_id] = request
    return {
        "run_id": request.spec.run_id,
        "status": "draft",
        "next_action": "POST /api/v1/runs/{run_id}/execute",
    }


@app.post("/api/v1/runs/{run_id}/execute")
def execute_run(run_id: str, round_id: str = Query(default="round_01")) -> dict[str, Any]:
    request = registry.payloads.get(run_id)
    if request is None:
        raise HTTPException(status_code=404, detail="run not found")
    effective_request = copy.deepcopy(request)
    # Native Aer extensions can be unsafe in some Python/ASGI thread pools.
    # Keep API execution safe by default; explicitly opt in after validating the
    # deployment with Q_DISCOVERY_API_ALLOW_QISKIT=1.
    if (
        effective_request.spec.solver.backend == "auto"
        and os.getenv("Q_DISCOVERY_API_ALLOW_QISKIT", "0") != "1"
    ):
        effective_request.spec.solver.backend = "fallback"
    try:
        result = AgentOrchestrator().run(
            effective_request.spec,
            effective_request.candidates,
            effective_request.observations,
            round_id=round_id,
        )
    except QDiscoveryError as error:
        raise HTTPException(
            status_code=422,
            detail={"error_code": getattr(error, "code", "PIPELINE_ERROR"), "message": str(error)},
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error_code": "PIPELINE_ERROR", "message": str(error)}) from error
    payload = result.model_dump(mode="json")
    registry.results[run_id] = payload
    return payload


@app.post("/api/v1/runs/{run_id}/jobs", status_code=202)
def create_job(run_id: str, round_id: str = Query(default="round_01")) -> dict[str, str]:
    if run_id not in registry.payloads:
        raise HTTPException(status_code=404, detail="run not found")

    def execute_in_job() -> dict[str, Any]:
        request = registry.payloads[run_id]
        effective_request = copy.deepcopy(request)
        if (
            effective_request.spec.solver.backend == "auto"
            and os.getenv("Q_DISCOVERY_API_ALLOW_QISKIT", "0") != "1"
        ):
            effective_request.spec.solver.backend = "fallback"
        result = AgentOrchestrator().run(
            effective_request.spec,
            effective_request.candidates,
            effective_request.observations,
            round_id=round_id,
        )
        payload = result.model_dump(mode="json")
        registry.results[run_id] = payload
        return payload

    job_id = job_runner.submit(execute_in_job)
    return {"job_id": job_id, "run_id": run_id, "status": "queued"}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    record = job_runner.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": record.job_id,
        "status": record.status,
        "result": record.result,
        "error": record.error,
    }


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    if run_id in registry.results:
        return registry.results[run_id]
    if run_id in registry.payloads:
        return {"run_id": run_id, "status": "draft"}
    raise HTTPException(status_code=404, detail="run not found")


@app.get("/api/v1/runs/{run_id}/recommendations")
def recommendations(run_id: str) -> dict[str, Any]:
    result = registry.results.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="run result not found")
    return {"run_id": run_id, "recommendations": result["recommendations"]}


@app.get("/api/v1/runs/{run_id}/verification")
def verification(run_id: str) -> dict[str, Any]:
    result = registry.results.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="run result not found")
    return {"run_id": run_id, "verification": result["verification"]}


@app.get("/api/v1/artifacts")
def get_artifact(artifact_id: str) -> Any:
    try:
        return artifact_store.read_json(artifact_id)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=404, detail="artifact not found") from error


@app.post("/api/v1/runs/{run_id}/rounds/{round_id}/observations")
def import_observations(run_id: str, round_id: str, request: ObservationImportRequest) -> dict[str, Any]:
    payload = registry.payloads.get(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="run not found")
    try:
        payload.observations = append_observations(
            payload.observations,
            request.observations,
            round_id,
            payload.candidates,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"error_code": "INVALID_OBSERVATIONS", "message": str(error)}) from error
    return {
        "run_id": run_id,
        "round_id": round_id,
        "imported_count": len(request.observations),
        "next_action": f"POST /api/v1/runs/{run_id}/execute?round_id={round_id}",
    }
