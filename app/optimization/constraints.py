from __future__ import annotations

from itertools import combinations

from app.domain.models import Candidate, ExperimentDesignSpec


def constraint_values(spec: ExperimentDesignSpec) -> dict[str, float | int | None]:
    result: dict[str, float | int | None] = {
        "cardinality": spec.cardinality(),
        "max_cost": spec.batch.total_budget,
        "max_runtime": spec.batch.max_runtime_minutes,
    }
    for constraint in spec.hard_constraints:
        if constraint.type == "max_cost":
            result["max_cost"] = float(constraint.value)
        elif constraint.type == "max_runtime":
            result["max_runtime"] = float(constraint.value)
    return result


def forbidden_pairs(spec: ExperimentDesignSpec) -> set[frozenset[str]]:
    return {
        frozenset({str(constraint.left), str(constraint.right)})
        for constraint in spec.hard_constraints
        if constraint.type == "forbidden_pair" and constraint.left and constraint.right
    }


def is_feasible(
    bitstring: list[int],
    candidates: list[Candidate],
    spec: ExperimentDesignSpec,
) -> tuple[bool, list[str]]:
    if len(bitstring) != len(candidates):
        return False, [f"bitstring length {len(bitstring)} does not match candidate count {len(candidates)}"]
    if any(bit not in (0, 1) for bit in bitstring):
        return False, ["bitstring values must be binary 0/1"]
    selected = [candidate for bit, candidate in zip(bitstring, candidates) if bit]
    reasons: list[str] = []
    values = constraint_values(spec)
    if len(selected) != int(values["cardinality"]):
        reasons.append(f"expected {values['cardinality']} selected, got {len(selected)}")
    if any(not candidate.availability for candidate in selected):
        reasons.append("selected unavailable candidate")
    max_cost = values["max_cost"]
    if max_cost is not None and sum(candidate.cost for candidate in selected) > float(max_cost) + 1e-9:
        reasons.append(f"cost exceeds {max_cost}")
    max_runtime = values["max_runtime"]
    if max_runtime is not None and sum(candidate.runtime_minutes or 0.0 for candidate in selected) > float(max_runtime) + 1e-9:
        reasons.append(f"runtime exceeds {max_runtime}")
    selected_ids = {candidate.candidate_id for candidate in selected}
    for pair in forbidden_pairs(spec):
        if pair.issubset(selected_ids):
            reasons.append(f"forbidden pair selected: {sorted(pair)}")
    required = {
        str(constraint.value)
        for constraint in spec.hard_constraints
        if constraint.type == "required_candidate"
    }
    if not required.issubset(selected_ids):
        reasons.append(f"missing required candidates: {sorted(required - selected_ids)}")
    return not reasons, reasons


def partial_constraints_ok(
    selected: list[Candidate],
    spec: ExperimentDesignSpec,
) -> tuple[bool, list[str]]:
    """Check constraints that can already be violated before cardinality is complete."""
    reasons: list[str] = []
    if any(not candidate.availability for candidate in selected):
        reasons.append("selected unavailable candidate")
    values = constraint_values(spec)
    if values["max_cost"] is not None and sum(candidate.cost for candidate in selected) > float(values["max_cost"]) + 1e-9:
        reasons.append(f"cost exceeds {values['max_cost']}")
    if values["max_runtime"] is not None and sum(candidate.runtime_minutes or 0.0 for candidate in selected) > float(values["max_runtime"]) + 1e-9:
        reasons.append(f"runtime exceeds {values['max_runtime']}")
    selected_ids = {candidate.candidate_id for candidate in selected}
    for pair in forbidden_pairs(spec):
        if pair.issubset(selected_ids):
            reasons.append(f"forbidden pair selected: {sorted(pair)}")
    return not reasons, reasons


def can_complete_selection(
    selected: list[Candidate],
    remaining: list[Candidate],
    spec: ExperimentDesignSpec,
) -> bool:
    needed = spec.cardinality() - len(selected)
    if needed < 0 or len(remaining) < needed:
        return False
    for combo in combinations(remaining, needed):
        bits = [int(candidate in (*selected, *combo)) for candidate in [*selected, *remaining]]
        if is_feasible(bits, [*selected, *remaining], spec)[0]:
            return True
    return False
