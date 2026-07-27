from __future__ import annotations

import math
import uuid

from app.domain.models import (
    AcquisitionConfig,
    Candidate,
    ModelPrediction,
    PreferenceWeights,
)


def _normalize(values: list[float], invert: bool = False) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        result = [0.5 for _ in values]
    else:
        result = [(value - low) / (high - low) for value in values]
    return [1.0 - item for item in result] if invert else result


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def build_acquisition(
    candidates: list[Candidate],
    predictions: list[ModelPrediction],
    weights: PreferenceWeights,
    objective_direction: str = "maximize",
    feature_rows: list[list[float]] | None = None,
) -> dict:
    prediction_by_id = {item.candidate_id: item for item in predictions}
    means = [prediction_by_id[item.candidate_id].mean for item in candidates]
    stds = [prediction_by_id[item.candidate_id].std for item in candidates]
    costs = [item.cost for item in candidates]
    risks = [item.risk for item in candidates]
    normalized_mean = _normalize([-value for value in means] if objective_direction == "minimize" else means)
    normalized_std = _normalize(stds)
    normalized_cost = _normalize(costs, invert=True)
    normalized_risk = _normalize(risks, invert=True)
    linear: dict[str, float] = {}
    for index, candidate in enumerate(candidates):
        linear[candidate.candidate_id] = (
            weights.exploitation * normalized_mean[index]
            + weights.exploration * normalized_std[index]
            + weights.cost * normalized_cost[index]
            + weights.risk * normalized_risk[index]
        )
    quadratic: dict[str, float] = {}
    feature_rows = feature_rows or [
        [float(value) for value in candidate.raw_features.values() if isinstance(value, (int, float))]
        for candidate in candidates
    ]
    # If the candidate has no numeric raw fields, use stable id-independent one-hot-like
    # values from the sorted feature values. This keeps diversity deterministic.
    fallback_vectors: list[list[float]] = []
    for candidate in candidates:
        if feature_rows[len(fallback_vectors)]:
            fallback_vectors.append(feature_rows[len(fallback_vectors)])
        else:
            fallback_vectors.append(
                [float(sum(ord(char) for char in str(value))) for value in candidate.raw_features.values()]
                or [0.0]
            )
    distances: list[float] = []
    for left_index in range(len(candidates)):
        for right_index in range(left_index + 1, len(candidates)):
            distances.append(_distance(fallback_vectors[left_index], fallback_vectors[right_index]))
    normalized_distances = _normalize(distances)
    cursor = 0
    for left_index in range(len(candidates)):
        for right_index in range(left_index + 1, len(candidates)):
            if normalized_distances[cursor] > 0.0:
                key = f"{candidates[left_index].candidate_id}|{candidates[right_index].candidate_id}"
                quadratic[key] = weights.diversity * normalized_distances[cursor]
            cursor += 1
    return {
        "acquisition_id": f"acq-{uuid.uuid4().hex[:10]}",
        "linear": linear,
        "quadratic": quadratic,
        "config": AcquisitionConfig(
            exploitation=weights.exploitation,
            exploration=weights.exploration,
            diversity=weights.diversity,
            cost=weights.cost,
            risk=weights.risk,
        ).model_dump(mode="json"),
        "objective_direction": objective_direction,
        "prediction_by_id": {key: value.model_dump(mode="json") for key, value in prediction_by_id.items()},
    }
