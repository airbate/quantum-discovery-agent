from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.domain.models import Candidate, Observation


def _number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def records_to_domain(
    records: list[dict[str, Any]],
    candidate_id_column: str = "candidate_id",
    target_column: str = "yield",
    feature_columns: list[str] | None = None,
    round_id: str = "round_00",
) -> tuple[list[Candidate], list[Observation]]:
    if not records:
        return [], []
    feature_columns = feature_columns or [
        key
        for key in records[0]
        if key not in {candidate_id_column, target_column, "cost", "risk", "runtime_minutes"}
    ]
    candidates: list[Candidate] = []
    observations: list[Observation] = []
    for raw in records:
        candidate_id = str(raw.get(candidate_id_column, "")).strip()
        if not candidate_id:
            raise ValueError(f"missing candidate id in row: {raw}")
        candidate = Candidate(
            candidate_id=candidate_id,
            raw_features={key: raw.get(key) for key in feature_columns},
            cost=_number(raw.get("cost")),
            risk=_number(raw.get("risk")),
            runtime_minutes=(
                _number(raw.get("runtime_minutes"))
                if raw.get("runtime_minutes") not in (None, "")
                else None
            ),
            availability=str(raw.get("available", raw.get("availability", "true"))).lower()
            not in {"false", "0", "no", "unavailable"},
            metadata={"source_row": raw},
        )
        candidates.append(candidate)
        target = raw.get(target_column)
        if target not in (None, ""):
            try:
                observations.append(
                    Observation(
                        candidate_id=candidate_id,
                        target=float(target),
                        round_id=round_id,
                        source="historical",
                    )
                )
            except (TypeError, ValueError):
                raise ValueError(
                    f"invalid target {raw.get(target_column)!r} for candidate {candidate_id}"
                )
    return candidates, observations


def load_candidates_csv(
    path: str | Path,
    candidate_id_column: str = "candidate_id",
    target_column: str = "yield",
    feature_columns: list[str] | None = None,
    round_id: str = "round_00",
) -> tuple[list[Candidate], list[Observation]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    return records_to_domain(
        records,
        candidate_id_column=candidate_id_column,
        target_column=target_column,
        feature_columns=feature_columns,
        round_id=round_id,
    )


def load_json_records(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    raise ValueError("JSON must contain a list or a records list")
