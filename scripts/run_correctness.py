from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.features import FeatureEncoder
from app.domain.models import (
    Candidate,
    CandidateSource,
    ExperimentDesignSpec,
    Observation,
)
from app.modeling.acquisition import build_acquisition
from app.modeling.surrogate import NearestEnsembleSurrogate
from app.optimization.qubo import compile_qubo, utility_for_bitstring
from app.service import ExperimentService
from app.verification.feasibility import verify_bitstring


def main() -> None:
    candidates = [
        Candidate(candidate_id=f"c{i}", raw_features={"x": i, "group": "A" if i % 2 else "B"}, cost=1)
        for i in range(6)
    ]
    observations = [Observation(candidate_id="c0", target=0.2), Observation(candidate_id="c1", target=0.4)]
    spec = ExperimentDesignSpec(
        run_id="correctness",
        name="correctness",
        candidate_source=CandidateSource(dataset_id="fixture", feature_columns=["x", "group"]),
        batch={"size": 2, "total_budget": 2},
    )
    table = FeatureEncoder(spec.candidate_source.feature_columns).fit(candidates).transform(candidates)
    model = NearestEnsembleSurrogate()
    model.fit(observations, table)
    problem = compile_qubo(candidates, spec, build_acquisition(candidates, model.predict(table), spec.preferences))
    feasible = []
    for indexes in itertools.combinations(range(len(candidates)), 2):
        bits = [int(index in indexes) for index in range(len(candidates))]
        report = verify_bitstring(bits, candidates, spec, problem, utility_for_bitstring(bits, problem))
        assert report.status == "passed"
        feasible.append(report.objective_recomputed)
    result = ExperimentService().run_round(spec, candidates, observations, include_enumeration=True)
    assert result.status.value == "verified"
    assert result.verification.is_feasible
    assert result.recommendations
    print(f"correctness passed: {len(feasible)} feasible combinations; best={max(feasible):.6f}")


if __name__ == "__main__":
    main()
