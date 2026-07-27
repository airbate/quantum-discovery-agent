from __future__ import annotations

import math
from typing import Any

from app.domain.models import Candidate, FeatureTable


class FeatureEncoder:
    """Stable, dependency-free mixed numeric/categorical feature encoder."""

    def __init__(self, feature_columns: list[str]):
        self.feature_columns = feature_columns
        self.category_maps: dict[str, dict[str, int]] = {}
        self.numeric_ranges: dict[str, tuple[float, float]] = {}
        self.feature_names: list[str] = []

    def fit(self, candidates: list[Candidate]) -> FeatureEncoder:
        self.category_maps = {}
        self.numeric_ranges = {}
        self.feature_names = []
        for column in self.feature_columns:
            values = [candidate.raw_features.get(column) for candidate in candidates]
            numeric_values: list[float] = []
            is_numeric = True
            for value in values:
                try:
                    numeric_values.append(float(value))
                except (TypeError, ValueError):
                    is_numeric = False
                    break
            if is_numeric and numeric_values:
                low, high = min(numeric_values), max(numeric_values)
                self.numeric_ranges[column] = (low, high)
                self.feature_names.append(column)
            else:
                labels = sorted({str(value) for value in values})
                self.category_maps[column] = {label: index for index, label in enumerate(labels)}
                self.feature_names.extend([f"{column}={label}" for label in labels])
        return self

    def transform(self, candidates: list[Candidate]) -> FeatureTable:
        rows: list[list[float]] = []
        for candidate in candidates:
            row: list[float] = []
            for column in self.feature_columns:
                value: Any = candidate.raw_features.get(column)
                if column in self.numeric_ranges:
                    low, high = self.numeric_ranges[column]
                    number = float(value)
                    row.append(0.5 if math.isclose(low, high) else (number - low) / (high - low))
                else:
                    mapping = self.category_maps[column]
                    encoded = str(value)
                    row.extend(1.0 if encoded == label else 0.0 for label in mapping)
            rows.append(row)
        return FeatureTable(
            candidate_ids=[candidate.candidate_id for candidate in candidates],
            rows=rows,
            feature_names=self.feature_names,
            category_maps=self.category_maps,
        )
