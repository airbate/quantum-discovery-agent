from app.domain.models import Candidate, CandidateSource, ExperimentDesignSpec
from app.optimization.baselines import (
    EnumerationSolver,
    GreedySolver,
    SimulatedAnnealingSolver,
)
from app.optimization.qubo import compile_qubo


def test_classical_solvers_return_feasible_batches():
    candidates = [
        Candidate(candidate_id="a", raw_features={"x": 0}, cost=1),
        Candidate(candidate_id="b", raw_features={"x": 1}, cost=1),
        Candidate(candidate_id="c", raw_features={"x": 2}, cost=1),
        Candidate(candidate_id="d", raw_features={"x": 3}, cost=1),
    ]
    spec = ExperimentDesignSpec(
        run_id="solver-test",
        name="solver",
        candidate_source=CandidateSource(dataset_id="fixture", feature_columns=["x"]),
        batch={"size": 2},
    )
    problem = compile_qubo(
        candidates,
        spec,
        {
            "acquisition_id": "test",
            "linear": {"a": 0.1, "b": 0.9, "c": 0.8, "d": 0.2},
            "quadratic": {},
        },
    )
    exact = EnumerationSolver().solve(problem, candidates, spec)
    greedy = GreedySolver().solve(problem, candidates, spec)
    annealing = SimulatedAnnealingSolver().solve(problem, candidates, spec, seed=7)
    assert sum(exact.best_bitstring) == 2
    assert sum(greedy.best_bitstring) == 2
    assert sum(annealing.best_bitstring) == 2
    assert exact.best_value >= greedy.best_value
