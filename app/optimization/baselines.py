from __future__ import annotations

import random
import time
from itertools import islice

from app.domain.errors import NoFeasibleBatchError
from app.domain.models import (
    Candidate,
    ExperimentDesignSpec,
    QUBOProblem,
    ResourceUsage,
    SolverArtifact,
    SolverKind,
)
from app.optimization.constraints import is_feasible, partial_constraints_ok
from app.optimization.qubo import feasible_bitstrings, utility_for_bitstring


def _artifact(
    kind: SolverKind,
    samples: list[dict],
    best: list[int],
    value: float,
    started: float,
    backend: str = "classical",
) -> SolverArtifact:
    return SolverArtifact(
        solver_kind=kind,
        samples=samples,
        best_bitstring=best,
        best_value=value,
        resource_usage=ResourceUsage(
            backend=backend,
            quantum_width=0,
            objective_calls=len(samples),
            wall_time_seconds=time.perf_counter() - started,
        ),
    )


class EnumerationSolver:
    def solve(self, problem: QUBOProblem, candidates: list[Candidate], spec: ExperimentDesignSpec, seed: int = 0) -> SolverArtifact:
        started = time.perf_counter()
        best_bits: list[int] | None = None
        best_value = float("-inf")
        samples: list[dict] = []
        for bits in feasible_bitstrings(candidates, spec):
            value = utility_for_bitstring(bits, problem)
            samples.append({"bitstring": bits, "value": value})
            if value > best_value:
                best_bits, best_value = bits, value
        if best_bits is None:
            raise NoFeasibleBatchError("no feasible batch exists")
        return _artifact(SolverKind.ENUMERATION, samples, best_bits, best_value, started)


class GreedySolver:
    def solve(self, problem: QUBOProblem, candidates: list[Candidate], spec: ExperimentDesignSpec, seed: int = 0) -> SolverArtifact:
        started = time.perf_counter()
        required_ids = {
            str(constraint.value)
            for constraint in spec.hard_constraints
            if constraint.type == "required_candidate"
        }
        selected: list[int] = [
            index for index, candidate in enumerate(candidates) if candidate.candidate_id in required_ids
        ]
        while len(selected) < spec.cardinality():
            best_index = None
            best_marginal = float("-inf")
            for index, candidate in enumerate(candidates):
                if index in selected:
                    continue
                trial = selected + [index]
                if not partial_constraints_ok([candidates[position] for position in trial], spec)[0]:
                    continue
                marginal = problem.linear.get(candidate.candidate_id, 0.0)
                for other_index in selected:
                    left = candidates[other_index].candidate_id
                    right = candidate.candidate_id
                    marginal += problem.quadratic.get(
                        f"{left}|{right}",
                        problem.quadratic.get(f"{right}|{left}", 0.0),
                    )
                if marginal > best_marginal:
                    best_index, best_marginal = index, marginal
            if best_index is None:
                break
            selected.append(best_index)
        bits = [int(position in selected) for position in range(len(candidates))]
        if not is_feasible(bits, candidates, spec)[0]:
            # A deterministic feasible fallback makes errors explicit rather than emitting a partial batch.
            enumeration = EnumerationSolver().solve(problem, candidates, spec, seed)
            enumeration.solver_kind = SolverKind.GREEDY
            enumeration.warnings.append("greedy could not complete; used exact feasible fallback")
            return enumeration
        value = utility_for_bitstring(bits, problem)
        return _artifact(SolverKind.GREEDY, [{"bitstring": bits, "value": value}], bits, value, started)


class ClassicalBatchBOSolver(GreedySolver):
    """Batch acquisition baseline using the compiled classical acquisition surface."""

    def solve(self, problem: QUBOProblem, candidates: list[Candidate], spec: ExperimentDesignSpec, seed: int = 0) -> SolverArtifact:
        artifact = super().solve(problem, candidates, spec, seed)
        artifact.solver_kind = SolverKind.CLASSICAL_BO
        artifact.resource_usage.backend = "classical_batch_acquisition"
        artifact.warnings.append("classical BO baseline uses the same observed-data acquisition coefficients")
        return artifact


class SimulatedAnnealingSolver:
    def solve(self, problem: QUBOProblem, candidates: list[Candidate], spec: ExperimentDesignSpec, seed: int = 0) -> SolverArtifact:
        started = time.perf_counter()
        rng = random.Random(seed)
        feasible = list(islice(feasible_bitstrings(candidates, spec), 2000))
        if not feasible:
            raise NoFeasibleBatchError("no feasible batch exists")
        current = list(rng.choice(feasible))
        current_value = utility_for_bitstring(current, problem)
        best, best_value = list(current), current_value
        samples: list[dict] = []
        for step in range(min(800, max(80, len(feasible) * 4))):
            proposal = list(rng.choice(feasible))
            proposal_value = utility_for_bitstring(proposal, problem)
            temperature = max(0.01, 1.0 - step / 800)
            if proposal_value >= current_value or rng.random() < temperature:
                current, current_value = proposal, proposal_value
            if current_value > best_value:
                best, best_value = list(current), current_value
            if step % 10 == 0:
                samples.append({"bitstring": list(current), "value": current_value})
        return _artifact(SolverKind.SIMULATED_ANNEALING, samples, best, best_value, started)
