from __future__ import annotations

from app.domain.models import (
    Candidate,
    ModelPrediction,
    QuantumNeighborhood,
    WarmStartArtifact,
)


def build_neighborhoods(
    candidates: list[Candidate],
    predictions: list[ModelPrediction],
    warm_start: WarmStartArtifact,
    max_width: int,
    count: int = 3,
) -> list[QuantumNeighborhood]:
    if len(candidates) <= max_width:
        return [
            QuantumNeighborhood(
                neighborhood_id="neighborhood_00",
                active_candidate_ids=[candidate.candidate_id for candidate in candidates],
                fixed_candidate_ids=[],
                local_cardinality=len(warm_start.candidate_ids),
                rationale=["full candidate pool fits quantum width"],
            )
        ]
    prediction_by_id = {item.candidate_id: item for item in predictions}
    warm_ids = set(warm_start.candidate_ids)
    ranked = sorted(
        candidates,
        key=lambda item: prediction_by_id[item.candidate_id].std,
        reverse=True,
    )
    neighborhoods: list[QuantumNeighborhood] = []
    for neighborhood_index in range(count):
        active: list[Candidate] = [candidate for candidate in candidates if candidate.candidate_id in warm_ids]
        for candidate in ranked:
            if candidate not in active:
                active.append(candidate)
            if len(active) >= max_width:
                break
        # Rotate exploration candidates so repeated neighborhoods do not have the same frontier.
        if neighborhood_index:
            rotated = ranked[neighborhood_index :]
            for candidate in rotated:
                if candidate in active:
                    continue
                active[-1] = candidate
                break
        active_ids = [candidate.candidate_id for candidate in active[:max_width]]
        neighborhoods.append(
            QuantumNeighborhood(
                neighborhood_id=f"neighborhood_{neighborhood_index:02d}",
                active_candidate_ids=active_ids,
                fixed_candidate_ids=[candidate.candidate_id for candidate in candidates if candidate.candidate_id not in active_ids],
                local_cardinality=min(len(warm_ids), len(active_ids)),
                rationale=["warm-start core", "high uncertainty frontier", "bounded quantum width"],
            )
        )
    return neighborhoods
