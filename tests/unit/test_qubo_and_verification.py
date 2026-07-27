from app.data.features import FeatureEncoder
from app.domain.models import (
    Candidate,
    CandidateSource,
    Constraint,
    ExperimentDesignSpec,
    Observation,
)
from app.modeling.acquisition import build_acquisition
from app.modeling.surrogate import NearestEnsembleSurrogate
from app.optimization.qubo import compile_qubo, utility_for_bitstring
from app.verification.feasibility import verify_bitstring


def make_fixture():
    candidates = [
        Candidate(candidate_id="a", raw_features={"temperature": 80, "solvent": "A"}, cost=1),
        Candidate(candidate_id="b", raw_features={"temperature": 100, "solvent": "B"}, cost=1),
        Candidate(candidate_id="c", raw_features={"temperature": 120, "solvent": "A"}, cost=1),
        Candidate(candidate_id="d", raw_features={"temperature": 140, "solvent": "C"}, cost=1),
    ]
    observations = [
        Observation(candidate_id="a", target=0.3),
        Observation(candidate_id="b", target=0.8),
    ]
    spec = ExperimentDesignSpec(
        run_id="qubo-test",
        name="qubo",
        candidate_source=CandidateSource(dataset_id="fixture", feature_columns=["temperature", "solvent"]),
        batch={"size": 2},
    )
    return candidates, observations, spec


def test_compiled_problem_has_expected_variables_and_verifiable_objective():
    candidates, observations, spec = make_fixture()
    table = FeatureEncoder(spec.candidate_source.feature_columns).fit(candidates).transform(candidates)
    model = NearestEnsembleSurrogate()
    model.fit(observations, table)
    predictions = model.predict(table)
    acquisition = build_acquisition(candidates, predictions, spec.preferences)
    problem = compile_qubo(candidates, spec, acquisition)
    bits = [0, 1, 1, 0]
    report = verify_bitstring(bits, candidates, spec, problem, utility_for_bitstring(bits, problem))
    assert problem.variable_ids == ["a", "b", "c", "d"]
    assert report.status == "passed"
    assert report.is_feasible is True
    assert report.objective_abs_error == 0


def test_forbidden_pair_is_rejected():
    candidates, observations, spec = make_fixture()
    spec.hard_constraints.append(Constraint(type="forbidden_pair", left="a", right="b"))
    table = FeatureEncoder(spec.candidate_source.feature_columns).fit(candidates).transform(candidates)
    model = NearestEnsembleSurrogate()
    model.fit(observations, table)
    problem = compile_qubo(candidates, spec, build_acquisition(candidates, model.predict(table), spec.preferences))
    report = verify_bitstring([1, 1, 0, 0], candidates, spec, problem, utility_for_bitstring([1, 1, 0, 0], problem))
    assert report.status == "failed"
    assert report.is_feasible is False
