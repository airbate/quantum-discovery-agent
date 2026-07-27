from app.data.ingest import load_candidates_csv
from app.domain.models import CandidateSource, ExperimentDesignSpec
from app.modeling.active_learning import append_observations
from app.service import ExperimentService


def test_two_round_active_learning_reuses_the_same_contract():
    candidates, observations = load_candidates_csv(
        "data/examples/demo_candidates.csv",
        feature_columns=["ligand", "solvent", "base", "temperature"],
    )
    history = observations[:8]
    spec = ExperimentDesignSpec(
        run_id="e2e-two-round",
        name="two round",
        candidate_source=CandidateSource(
            dataset_id="demo",
            feature_columns=["ligand", "solvent", "base", "temperature"],
        ),
        batch={"size": 3, "total_budget": 5},
        solver={"backend": "fallback", "shots": 64, "max_quantum_width": 16},
    )
    service = ExperimentService()
    first = service.run_round(spec, candidates, history, round_id="round_01")
    assert first.verification.is_feasible
    assert first.recommendations
    new_observations = [
        observations[8].model_copy(update={"source": "user_import"}),
        observations[9].model_copy(update={"source": "user_import"}),
    ]
    updated_history = append_observations(history, new_observations, "round_02", candidates)
    second = service.run_round(spec, candidates, updated_history, round_id="round_02")
    assert second.verification.is_feasible
    assert second.round_id == "round_02"
    assert second.model_report.observation_count == len(updated_history)
