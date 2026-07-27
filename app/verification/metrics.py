from __future__ import annotations

import math
import statistics
from itertools import combinations

from app.domain.models import (
    BaselineResult,
    Candidate,
    ExperimentDesignSpec,
    SolverArtifact,
    StabilitySummary,
)
from app.optimization.constraints import is_feasible


def baseline_result(artifact: SolverArtifact, candidates: list[Candidate], spec: ExperimentDesignSpec) -> BaselineResult:
    return BaselineResult(
        solver_kind=artifact.solver_kind,
        best_value=artifact.best_value,
        feasible=is_feasible(artifact.best_bitstring, candidates, spec)[0],
        runtime_seconds=artifact.resource_usage.wall_time_seconds,
        metadata={"backend": artifact.resource_usage.backend, "fallback": artifact.resource_usage.fallback},
    )


def stability_summary(artifacts: list[SolverArtifact], candidates: list[Candidate], spec: ExperimentDesignSpec) -> StabilitySummary:
    if not artifacts:
        return StabilitySummary()
    values = [artifact.best_value for artifact in artifacts]
    feasible_count = sum(is_feasible(artifact.best_bitstring, candidates, spec)[0] for artifact in artifacts)
    return StabilitySummary(
        seed_count=len(artifacts),
        feasible_rate=feasible_count / len(artifacts),
        best_value_mean=statistics.fmean(values),
        best_value_std=statistics.pstdev(values) if len(values) > 1 else 0.0,
    )


def batch_diversity(bitstring: list[int], candidates: list[Candidate]) -> float:
    selected = [candidate for bit, candidate in zip(bitstring, candidates) if bit]
    if len(selected) < 2:
        return 0.0
    vectors = []
    for candidate in selected:
        vector = []
        for value in candidate.raw_features.values():
            try:
                vector.append(float(value))
            except (TypeError, ValueError):
                vector.append(float(sum(ord(char) for char in str(value)) % 997) / 997.0)
        vectors.append(vector or [0.0])
    distances = []
    for left, right in combinations(vectors, 2):
        distances.append(math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right))))
    return statistics.fmean(distances) if distances else 0.0


def compare_bitstrings(artifacts: list[SolverArtifact]) -> list[dict]:
    return [
        {
            "solver": artifact.solver_kind.value,
            "best_value": artifact.best_value,
            "runtime_seconds": artifact.resource_usage.wall_time_seconds,
            "backend": artifact.resource_usage.backend,
            "fallback": artifact.resource_usage.fallback,
        }
        for artifact in artifacts
    ]


def simple_regret(selected_ids: list[str], predictions: list[tuple[str, float]]) -> float:
    values = {candidate_id: value for candidate_id, value in predictions}
    if not values:
        return 0.0
    selected_value = max((values[item] for item in selected_ids if item in values), default=min(values.values()))
    return max(values.values()) - selected_value


def pareto_hypervolume(points: list[tuple[float, float]], reference: tuple[float, float] = (0.0, 0.0)) -> float:
    """2D hypervolume for (benefit, diversity) points above a reference."""
    if not points:
        return 0.0
    ordered = sorted(points, key=lambda point: point[0], reverse=True)
    volume = 0.0
    previous_x = reference[0]
    for x, y in ordered:
        if x <= reference[0] or y <= reference[1]:
            continue
        volume += max(0.0, x - previous_x) * max(0.0, y - reference[1])
        previous_x = x
    return volume
