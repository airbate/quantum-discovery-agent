from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from app.domain.models import ExperimentDesignSpec
from app.service import ExperimentService


def parse_experiment_goal(text: str, default_batch_size: int = 5) -> dict[str, Any]:
    """Deterministic parser used by the MVP; an LLM adapter can replace it.

    The parser extracts only safe, typed fields. It never evaluates text as code.
    """
    batch_match = re.search(r"(?:选择|选|batch|批次|实验数)\s*(?:恰好)?\s*(\d+)\s*(?:个|次|experiments?)?", text, re.IGNORECASE)
    budget_match = re.search(
        r"(?:预算|(?:总)?成本|budget|cost)\s*"
        r"(?:不超过|不高于|不大于|上限|<=|≤)?\s*"
        r"[:：=]?\s*(\d+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    size = int(batch_match.group(1)) if batch_match else default_batch_size
    budget = float(budget_match.group(1)) if budget_match else None
    direction = "minimize" if any(word in text.lower() for word in ["最小", "降低", "minimize", "minimise"]) else "maximize"
    return {
        "batch_size": size,
        "total_budget": budget,
        "objective_direction": direction,
        "objective_text": text.strip(),
        "warnings": [] if batch_match else [f"could not find batch size; defaulted to {default_batch_size}"],
    }


class AgentOrchestrator:
    """Traceable, deterministic orchestration around the application service."""

    def __init__(self, service: ExperimentService | None = None):
        self.service = service or ExperimentService()

    def run(
        self,
        spec: ExperimentDesignSpec,
        candidates: list,
        observations: list,
        round_id: str = "round_01",
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ):
        events: list[dict[str, Any]] = []

        def emit(tool: str, status: str, **payload: Any) -> None:
            event = {"tool_name": tool, "status": status, "run_id": spec.run_id, **payload}
            events.append(event)
            if event_sink:
                event_sink(event)

        emit("validate_design_spec", "success", next_allowed_tools=["audit_dataset"])
        emit("audit_dataset", "started")
        try:
            result = self.service.run_round(spec, candidates, observations, round_id)
        except Exception as error:
            emit(
                "run_pipeline",
                "failed",
                error_code=getattr(error, "code", "PIPELINE_ERROR"),
                message=str(error),
                recoverable=False,
            )
            raise
        emit("audit_dataset", "success", next_allowed_tools=["fit_surrogate"])
        emit("fit_surrogate", "success", model_id=result.model_report.model_id, next_allowed_tools=["compile_qubo"])
        emit("compile_qubo", "success", next_allowed_tools=["solve_batch"])
        scoring_artifacts = [
            artifact.resource_usage
            for artifact in result.solver_artifacts
            if "qiskit_aer" in artifact.resource_usage.backend
        ]
        emit(
            "evaluate_qubo_batch",
            "success",
            backends=sorted({usage.backend for usage in scoring_artifacts}),
            fallback=any(usage.fallback for usage in scoring_artifacts),
            next_allowed_tools=["solve_batch"],
        )
        emit("solve_batch", "success", solver_count=len(result.solver_artifacts), next_allowed_tools=["verify_solution"])
        emit(
            "verify_solution",
            "success" if result.verification.status != "failed" else "failed",
            feasible=result.verification.is_feasible,
            next_allowed_tools=["export_run_report"],
        )
        emit(
            "export_run_report",
            "success",
            recommendation_variant_count=len(result.recommendations),
            primary_candidate_count=len(result.recommendations[0].candidate_ids) if result.recommendations else 0,
        )
        result.agent_events = events
        if self.service.artifact_store is not None:
            event_artifact = self.service.artifact_store.write_json(
                spec.run_id,
                round_id,
                "agent_events",
                events,
            )
            base_artifacts = [
                artifact_id
                for artifact_id in result.verification.artifact_ids
                if "/agent_events.json#" not in artifact_id and "/manifest.json#" not in artifact_id
            ]
            manifest_id = self.service.artifact_store.write_json(
                spec.run_id,
                round_id,
                "manifest",
                {
                    "run_id": spec.run_id,
                    "round_id": round_id,
                    "status": result.status.value,
                    "dataset_id": spec.candidate_source.dataset_id,
                    "artifact_ids": base_artifacts + [event_artifact],
                    "agent_event_count": len(events),
                },
            )
            result.verification.artifact_ids = base_artifacts + [event_artifact, manifest_id]
        return result
