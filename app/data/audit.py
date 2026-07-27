from __future__ import annotations

import math
from collections import Counter
from typing import Any

from app.domain.errors import ValidationError
from app.domain.models import Candidate, ExperimentDesignSpec, Observation


def audit_candidates(
    candidates: list[Candidate],
    observations: list[Observation],
    spec: ExperimentDesignSpec,
) -> dict[str, Any]:
    if not candidates:
        raise ValidationError("dataset contains no candidates")
    ids = [candidate.candidate_id for candidate in candidates]
    duplicates = sorted([key for key, count in Counter(ids).items() if count > 1])
    if duplicates:
        raise ValidationError(f"duplicate candidate ids: {duplicates}")
    candidate_ids = set(ids)
    unknown_observations = sorted(
        {observation.candidate_id for observation in observations} - candidate_ids
    )
    if unknown_observations:
        raise ValidationError(f"observations reference unknown candidates: {unknown_observations}")
    available = [candidate for candidate in candidates if candidate.availability]
    missing_features = {
        column: sum(candidate.raw_features.get(column) in (None, "") for candidate in candidates)
        for column in spec.candidate_source.feature_columns
    }
    target_values = [item.target for item in observations]
    abnormal_targets = sum(not math.isfinite(value) for value in target_values)
    required = [
        str(constraint.value)
        for constraint in spec.hard_constraints
        if constraint.type == "required_candidate"
    ]
    missing_required = sorted(set(required) - candidate_ids)
    if missing_required:
        raise ValidationError(f"required candidates not found: {missing_required}")
    max_cost = next(
        (float(constraint.value) for constraint in spec.hard_constraints if constraint.type == "max_cost"),
        spec.batch.total_budget,
    )
    max_runtime = next(
        (
            float(constraint.value)
            for constraint in spec.hard_constraints
            if constraint.type == "max_runtime"
        ),
        spec.batch.max_runtime_minutes,
    )
    return {
        "candidate_count": len(candidates),
        "available_candidate_count": len(available),
        "observation_count": len(observations),
        "observed_candidate_count": len({item.candidate_id for item in observations}),
        "duplicate_candidate_ids": duplicates,
        "unknown_observations": unknown_observations,
        "feature_columns": spec.candidate_source.feature_columns,
        "target_column": spec.candidate_source.observed_target_column,
        "missing_features": missing_features,
        "abnormal_target_count": abnormal_targets,
        "batch_size": spec.cardinality(),
        "max_cost": max_cost,
        "max_runtime_minutes": max_runtime,
        "warnings": [
            *(["fewer than two observations; predictions will use a global prior"] if len(observations) < 2 else []),
            *(["one or more feature columns contain missing values"] if any(missing_features.values()) else []),
            *(["one or more target values are non-finite"] if abnormal_targets else []),
        ],
    }
