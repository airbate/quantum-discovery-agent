from __future__ import annotations

from app.domain.errors import NoFeasibleBatchError
from app.domain.models import (
    Candidate,
    ExperimentDesignSpec,
    QUBOProblem,
    WarmStartArtifact,
)
from app.optimization.constraints import is_feasible
from app.optimization.qubo import utility_for_bitstring


def build_warm_start(
    problem: QUBOProblem,
    candidates: list[Candidate],
    spec: ExperimentDesignSpec,
    seed: int = 0,
) -> WarmStartArtifact:
    selected: list[int] = []
    remaining = set(range(len(candidates)))
    while len(selected) < spec.cardinality() and remaining:
        best_index: int | None = None
        best_value = float("-inf")
        for index in sorted(remaining):
            trial = selected + [index]
            bits = [int(position in trial) for position in range(len(candidates))]
            # Partial selection may not satisfy exact cardinality. Only enforce
            # constraints that can already be violated and check the final state.
            candidate = candidates[index]
            if not candidate.availability:
                continue
            selected_ids = {candidates[position].candidate_id for position in trial}
            if any(
                pair.issubset(selected_ids)
                for pair in {
                    frozenset(item["pair"])
                    for item in problem.metadata.get("forbidden_pairs", [])
                }
            ):
                continue
            marginal = problem.linear.get(candidate.candidate_id, 0.0)
            for other in selected:
                key = f"{candidates[other].candidate_id}|{candidate.candidate_id}"
                reverse_key = f"{candidate.candidate_id}|{candidates[other].candidate_id}"
                marginal += problem.quadratic.get(key, problem.quadratic.get(reverse_key, 0.0))
            if marginal > best_value:
                best_index, best_value = index, marginal
        if best_index is None:
            break
        selected.append(best_index)
        remaining.remove(best_index)
    bits = [int(position in selected) for position in range(len(candidates))]
    if not is_feasible(bits, candidates, spec)[0]:
        from app.optimization.qubo import feasible_bitstrings

        fallback = next(feasible_bitstrings(candidates, spec), None)
        if fallback is None:
            raise NoFeasibleBatchError("greedy warm start could not satisfy constraints")
        bits = fallback
    return WarmStartArtifact(
        bitstring=bits,
        candidate_ids=[candidate.candidate_id for bit, candidate in zip(bits, candidates) if bit],
        utility=utility_for_bitstring(bits, problem),
        method="greedy_feasible_warm_start",
        seed=seed,
    )
