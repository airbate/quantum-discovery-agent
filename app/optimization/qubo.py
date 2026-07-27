from __future__ import annotations

import itertools
from typing import Any

from app.domain.errors import NoFeasibleBatchError
from app.domain.models import (
    Candidate,
    CompiledConstraint,
    ConstraintMode,
    ExperimentDesignSpec,
    QUBOProblem,
)
from app.optimization.constraints import constraint_values, forbidden_pairs, is_feasible


def compile_qubo(
    candidates: list[Candidate],
    spec: ExperimentDesignSpec,
    acquisition: dict[str, Any],
) -> QUBOProblem:
    values = constraint_values(spec)
    available = [candidate for candidate in candidates if candidate.availability]
    if len(available) < spec.cardinality():
        raise NoFeasibleBatchError("not enough available candidates for requested batch")
    constraints = [
        CompiledConstraint(
            constraint_type="exact_cardinality",
            mode=ConstraintMode.EXACT_SUBSPACE,
            source="ExperimentDesignSpec.batch.size",
            metadata={"value": spec.cardinality()},
        )
    ]
    if values["max_cost"] is not None:
        constraints.append(
            CompiledConstraint(
                constraint_type="max_cost",
                mode=ConstraintMode.PRE_FILTER,
                source="ExperimentDesignSpec.batch.total_budget",
                metadata={"value": values["max_cost"]},
            )
        )
    for pair in forbidden_pairs(spec):
        constraints.append(
            CompiledConstraint(
                constraint_type="forbidden_pair",
                mode=ConstraintMode.PENALTY,
                source="ExperimentDesignSpec.hard_constraints",
                penalty=10.0,
                metadata={"pair": sorted(pair)},
            )
        )
    allowed_ids = {item.candidate_id for item in available}
    quadratic = {
        key: float(value)
        for key, value in acquisition["quadratic"].items()
        if all(part in allowed_ids for part in key.split("|"))
    }
    for pair in forbidden_pairs(spec):
        left, right = sorted(pair)
        if left in allowed_ids and right in allowed_ids:
            key = f"{left}|{right}"
            quadratic[key] = quadratic.get(key, 0.0) - 10.0
    return QUBOProblem(
        problem_id=f"qubo-{spec.run_id}-{len(available)}",
        variable_ids=[candidate.candidate_id for candidate in available],
        linear={key: float(value) for key, value in acquisition["linear"].items() if key in {item.candidate_id for item in available}},
        quadratic=quadratic,
        objective_direction="maximize",
        constraints=constraints,
        source_acquisition_id=acquisition["acquisition_id"],
        metadata={
            "cardinality": spec.cardinality(),
            "max_cost": values["max_cost"],
            "max_runtime": values["max_runtime"],
            "forbidden_pairs": [sorted(pair) for pair in forbidden_pairs(spec)],
        },
    )


def utility_for_bitstring(bitstring: list[int], problem: QUBOProblem) -> float:
    if len(bitstring) != len(problem.variable_ids) or any(bit not in (0, 1) for bit in bitstring):
        raise ValueError("bitstring must be binary and match QUBO variable count")
    value = problem.constant
    for index, candidate_id in enumerate(problem.variable_ids):
        if bitstring[index]:
            value += problem.linear.get(candidate_id, 0.0)
    for key, coefficient in problem.quadratic.items():
        left, right = key.split("|", 1)
        if bitstring[problem.variable_ids.index(left)] and bitstring[problem.variable_ids.index(right)]:
            value += coefficient
    return value


def feasible_bitstrings(candidates: list[Candidate], spec: ExperimentDesignSpec):
    count = len(candidates)
    for selected_indexes in itertools.combinations(range(count), spec.cardinality()):
        bitstring = [0] * count
        for index in selected_indexes:
            bitstring[index] = 1
        if is_feasible(bitstring, candidates, spec)[0]:
            yield bitstring
