from app.data.audit import audit_candidates
from app.data.features import FeatureEncoder
from app.data.ingest import records_to_domain
from app.domain.models import CandidateSource, ExperimentDesignSpec


def make_spec(size: int = 2) -> ExperimentDesignSpec:
    return ExperimentDesignSpec(
        run_id="test-run",
        name="test",
        candidate_source=CandidateSource(dataset_id="fixture", feature_columns=["temperature", "solvent"]),
        batch={"size": size},
    )


def test_records_are_loaded_and_audited():
    candidates, observations = records_to_domain(
        [
            {"candidate_id": "a", "temperature": "80", "solvent": "A", "yield": "0.4"},
            {"candidate_id": "b", "temperature": "100", "solvent": "B", "yield": "0.7"},
            {"candidate_id": "c", "temperature": "120", "solvent": "A"},
        ],
        feature_columns=["temperature", "solvent"],
    )
    report = audit_candidates(candidates, observations, make_spec())
    assert report["candidate_count"] == 3
    assert report["observation_count"] == 2

    table = FeatureEncoder(["temperature", "solvent"]).fit(candidates).transform(candidates)
    assert table.candidate_ids == ["a", "b", "c"]
    assert len(table.rows) == 3
    assert all(len(row) == len(table.feature_names) for row in table.rows)
