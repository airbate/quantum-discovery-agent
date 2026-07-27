from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import Candidate, Observation


@dataclass(frozen=True)
class ActiveLearningRound:
    round_id: str
    observations: tuple[Observation, ...]


def append_observations(
    history: list[Observation],
    new_observations: list[Observation],
    round_id: str,
    candidates: list[Candidate],
) -> list[Observation]:
    """Validate and append one observation round without leaking hidden labels."""
    candidate_ids = {candidate.candidate_id for candidate in candidates}
    unknown = sorted({item.candidate_id for item in new_observations} - candidate_ids)
    if unknown:
        raise ValueError(f"unknown candidates: {unknown}")
    existing = {(item.round_id, item.candidate_id) for item in history}
    appended = list(history)
    for observation in new_observations:
        key = (round_id, observation.candidate_id)
        if key in existing:
            raise ValueError(f"duplicate observation: {key}")
        appended.append(observation.model_copy(update={"round_id": round_id, "source": "user_import"}))
        existing.add(key)
    return appended
