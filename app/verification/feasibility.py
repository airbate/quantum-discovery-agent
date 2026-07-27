from __future__ import annotations

from app.domain.models import (
    Candidate,
    ConstraintResult,
    ExperimentDesignSpec,
    QUBOProblem,
    VerificationReport,
)
from app.optimization.constraints import is_feasible
from app.optimization.qubo import utility_for_bitstring


def verify_bitstring(
    bitstring: list[int],
    candidates: list[Candidate],
    spec: ExperimentDesignSpec,
    problem: QUBOProblem,
    reported_value: float,
) -> VerificationReport:
    feasible, reasons = is_feasible(bitstring, candidates, spec)
    results = [
        ConstraintResult(
            constraint_type="hard_constraints",
            passed=feasible,
            detail="all hard constraints passed" if feasible else "; ".join(reasons),
        )
    ]
    try:
        recomputed = utility_for_bitstring(bitstring, problem)
        error = abs(recomputed - reported_value)
    except ValueError as error_value:
        recomputed = float("nan")
        error = float("inf")
        results.append(
            ConstraintResult(
                constraint_type="bitstring_shape",
                passed=False,
                detail=str(error_value),
            )
        )
    if error > 1e-8:
        results.append(
            ConstraintResult(
                constraint_type="objective_consistency",
                passed=False,
                detail=f"reported={reported_value:.12g}, recomputed={recomputed:.12g}",
            )
        )
    else:
        results.append(
            ConstraintResult(
                constraint_type="objective_consistency",
                passed=True,
                detail="objective was independently recomputed",
            )
        )
    status = "passed" if feasible and error <= 1e-8 else "failed"
    return VerificationReport(
        status=status,
        hard_constraint_results=results,
        objective_recomputed=recomputed,
        objective_reported=reported_value,
        objective_abs_error=error,
        is_feasible=feasible,
        warnings=[] if status == "passed" else ["solution must not be published as a recommendation"],
    )
