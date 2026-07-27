from __future__ import annotations

import math
import statistics
import uuid

from app.domain.errors import ModelInsufficientDataError
from app.domain.models import (
    FeatureTable,
    ModelFitReport,
    ModelPrediction,
    Observation,
)


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


class NearestEnsembleSurrogate:
    """Small-data surrogate with distance-weighted predictions and uncertainty.

    It intentionally has no heavy numerical dependency so the demo can run in a
    clean contest environment. A GP/ensemble adapter can replace it later.
    """

    def __init__(self, minimum_observations: int = 1):
        self.minimum_observations = minimum_observations
        self.model_id = f"nearest-ensemble-{uuid.uuid4().hex[:8]}"
        self.observation_features: list[list[float]] = []
        self.observation_values: list[float] = []
        self.observation_ids: list[str] = []
        self.global_mean = 0.0
        self.global_std = 0.25

    def fit(self, observations: list[Observation], features: FeatureTable) -> ModelFitReport:
        if len(observations) < self.minimum_observations:
            raise ModelInsufficientDataError(
                f"need at least {self.minimum_observations} observations, got {len(observations)}"
            )
        by_id = {candidate_id: row for candidate_id, row in zip(features.candidate_ids, features.rows)}
        selected = [item for item in observations if item.candidate_id in by_id]
        if not selected:
            raise ModelInsufficientDataError("no observations overlap with feature table")
        self.observation_features = [by_id[item.candidate_id] for item in selected]
        self.observation_values = [item.target for item in selected]
        self.observation_ids = [f"{item.round_id}:{item.candidate_id}" for item in selected]
        self.global_mean = statistics.fmean(self.observation_values)
        self.global_std = statistics.pstdev(self.observation_values) if len(selected) > 1 else 0.2
        return ModelFitReport(
            model_id=self.model_id,
            observation_count=len(selected),
            feature_count=len(features.feature_names),
            metrics={"training_mean": self.global_mean, "training_std": self.global_std},
            warnings=(
                ["single-observation prior; uncertainty is conservative"]
                if len(selected) == 1
                else []
            ),
        )

    def predict(self, features: FeatureTable) -> list[ModelPrediction]:
        predictions: list[ModelPrediction] = []
        for candidate_id, row in zip(features.candidate_ids, features.rows):
            distances = sorted(
                (_distance(row, observed), value)
                for observed, value in zip(self.observation_features, self.observation_values)
            )
            nearest = distances[: min(5, len(distances))]
            if nearest:
                weights = [1.0 / (distance + 0.05) for distance, _ in nearest]
                mean = sum(weight * value for weight, (_, value) in zip(weights, nearest)) / sum(weights)
                local_values = [value for _, value in nearest]
                local_std = statistics.pstdev(local_values) if len(local_values) > 1 else self.global_std
                uncertainty = max(0.02, local_std + min(0.2, nearest[0][0] * 0.15))
            else:
                mean, uncertainty = self.global_mean, self.global_std
            predictions.append(
                ModelPrediction(
                    candidate_id=candidate_id,
                    mean=mean,
                    std=uncertainty,
                    lower_bound=mean - 1.96 * uncertainty,
                    upper_bound=mean + 1.96 * uncertainty,
                    model_id=self.model_id,
                    training_observation_ids=self.observation_ids,
                )
            )
        return predictions
