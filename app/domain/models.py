from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RunStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    MODELED = "modeled"
    COMPILED = "compiled"
    SOLVED = "solved"
    VERIFIED = "verified"
    PRESENTED = "presented"
    UPDATED = "updated"
    FAILED = "failed"


class SolverKind(str, Enum):
    ENUMERATION = "enumeration"
    GREEDY = "greedy"
    SIMULATED_ANNEALING = "simulated_annealing"
    CLASSICAL_BO = "classical_bo"
    PENALTY_QAOA = "penalty_qaoa"
    WARM_START_XY_QAOA = "warm_start_xy_qaoa"


class ConstraintMode(str, Enum):
    PRE_FILTER = "pre_filter"
    EXACT_SUBSPACE = "exact_subspace"
    PENALTY = "penalty"
    SLACK_QUBO = "slack_qubo"


class Candidate(StrictModel):
    candidate_id: str = Field(min_length=1)
    raw_features: dict[str, Any] = Field(default_factory=dict)
    cost: float = Field(default=0.0, ge=0.0)
    risk: float = Field(default=0.0, ge=0.0)
    runtime_minutes: float | None = Field(default=None, ge=0.0)
    availability: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(StrictModel):
    candidate_id: str
    target: float
    round_id: str = "round_00"
    source: Literal["historical", "simulated_oracle", "user_import"] = "historical"
    observed_at: datetime | None = None
    quality_flags: list[str] = Field(default_factory=list)


class Constraint(StrictModel):
    type: Literal[
        "exact_cardinality",
        "max_cost",
        "max_runtime",
        "forbidden_pair",
        "required_candidate",
    ]
    value: float | int | str | None = None
    left: str | None = None
    right: str | None = None


class PreferenceWeights(StrictModel):
    exploitation: float = Field(default=0.4, ge=0.0)
    exploration: float = Field(default=0.25, ge=0.0)
    diversity: float = Field(default=0.2, ge=0.0)
    cost: float = Field(default=0.1, ge=0.0)
    risk: float = Field(default=0.05, ge=0.0)

    @field_validator("risk")
    @classmethod
    def weights_not_all_zero(cls, value: float) -> float:
        return value

    def total(self) -> float:
        return (
            self.exploitation
            + self.exploration
            + self.diversity
            + self.cost
            + self.risk
        )


class SolverConfig(StrictModel):
    kind: SolverKind = SolverKind.WARM_START_XY_QAOA
    max_quantum_width: int = Field(default=16, ge=2, le=28)
    p: int = Field(default=2, ge=1, le=5)
    shots: int = Field(default=512, ge=32, le=100_000)
    angle_optimizer: Literal["bayesian", "random", "grid"] = "bayesian"
    max_objective_calls: int = Field(default=24, ge=1, le=200)
    seed: int = 20260727
    backend: str = "auto"
    qubo_evaluation_device: Literal["cpu", "supa", "auto"] = "auto"
    noise_model: Literal["none", "depolarizing"] = "none"


class CandidateSource(StrictModel):
    dataset_id: str
    candidate_id_column: str = "candidate_id"
    feature_columns: list[str]
    observed_target_column: str = "yield"


class ObjectiveSpec(StrictModel):
    metric: str = "yield"
    direction: Literal["maximize", "minimize"] = "maximize"
    unit: str = "fraction"


class BatchSpec(StrictModel):
    size: int = Field(default=5, ge=1)
    total_budget: float | None = Field(default=None, ge=0.0)
    max_runtime_minutes: float | None = Field(default=None, ge=0.0)


class ExperimentDesignSpec(StrictModel):
    run_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    domain: str = "reaction_condition_optimization"
    objective: ObjectiveSpec = Field(default_factory=ObjectiveSpec)
    candidate_source: CandidateSource
    batch: BatchSpec = Field(default_factory=BatchSpec)
    preferences: PreferenceWeights = Field(default_factory=PreferenceWeights)
    hard_constraints: list[Constraint] = Field(default_factory=list)
    solver: SolverConfig = Field(default_factory=SolverConfig)

    def cardinality(self) -> int:
        exact = [c for c in self.hard_constraints if c.type == "exact_cardinality"]
        if exact:
            return int(exact[0].value)
        return self.batch.size


class FeatureTable(StrictModel):
    candidate_ids: list[str]
    rows: list[list[float]]
    feature_names: list[str]
    category_maps: dict[str, dict[str, int]] = Field(default_factory=dict)


class ModelPrediction(StrictModel):
    candidate_id: str
    mean: float
    std: float = Field(ge=0.0)
    lower_bound: float
    upper_bound: float
    model_id: str
    training_observation_ids: list[str] = Field(default_factory=list)


class ModelFitReport(StrictModel):
    model_id: str
    observation_count: int = Field(ge=0)
    feature_count: int = Field(ge=0)
    metrics: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class AcquisitionConfig(StrictModel):
    exploitation: float
    exploration: float
    diversity: float
    cost: float
    risk: float
    distance_metric: Literal["euclidean", "cosine"] = "euclidean"
    sparse_neighbors: int = Field(default=8, ge=1)


class CompiledConstraint(StrictModel):
    constraint_type: str
    mode: ConstraintMode
    source: str
    penalty: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QUBOProblem(StrictModel):
    problem_id: str
    variable_ids: list[str]
    linear: dict[str, float] = Field(default_factory=dict)
    quadratic: dict[str, float] = Field(default_factory=dict)
    constant: float = 0.0
    objective_direction: Literal["minimize", "maximize"] = "maximize"
    constraints: list[CompiledConstraint] = Field(default_factory=list)
    source_acquisition_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QUBOBatchEvaluation(StrictModel):
    values: list[float]
    backend: Literal["python_cpu", "torch_supa"]
    device_count: int = 0
    wall_time_seconds: float = Field(default=0.0, ge=0.0)
    fallback: bool = False
    warnings: list[str] = Field(default_factory=list)


class WarmStartArtifact(StrictModel):
    bitstring: list[int]
    candidate_ids: list[str]
    utility: float
    method: str
    seed: int


class ResourceUsage(StrictModel):
    backend: str
    quantum_width: int = 0
    circuit_depth: int = 0
    shots: int = 0
    objective_calls: int = 0
    wall_time_seconds: float = 0.0
    fallback: bool = False
    warnings: list[str] = Field(default_factory=list)


class CandidateBatch(StrictModel):
    batch_id: str
    strategy: str = "primary"
    candidate_ids: list[str]
    predicted_components: dict[str, float] = Field(default_factory=dict)
    predicted_objective: float
    solver_kind: SolverKind
    sample_probability: float | None = None
    resource_usage: ResourceUsage


class SolverArtifact(StrictModel):
    solver_kind: SolverKind
    samples: list[dict[str, Any]]
    best_bitstring: list[int]
    best_value: float
    resource_usage: ResourceUsage
    warnings: list[str] = Field(default_factory=list)


class ConstraintResult(StrictModel):
    constraint_type: str
    passed: bool
    detail: str


class BaselineResult(StrictModel):
    solver_kind: SolverKind
    best_value: float | None = None
    feasible: bool = False
    runtime_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class StabilitySummary(StrictModel):
    seed_count: int = 0
    feasible_rate: float = 0.0
    best_value_mean: float | None = None
    best_value_std: float | None = None


class VerificationReport(StrictModel):
    status: Literal["passed", "failed", "warning"]
    hard_constraint_results: list[ConstraintResult]
    objective_recomputed: float
    objective_reported: float
    objective_abs_error: float
    is_feasible: bool
    baseline_comparison: list[BaselineResult] = Field(default_factory=list)
    stability: StabilitySummary = Field(default_factory=StabilitySummary)
    warnings: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class RunManifest(StrictModel):
    run_id: str
    round_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: RunStatus = RunStatus.DRAFT
    dataset_id: str
    config_hash: str
    artifact_ids: list[str] = Field(default_factory=list)
    dependency_versions: dict[str, str] = Field(default_factory=dict)


class QuantumNeighborhood(StrictModel):
    neighborhood_id: str
    active_candidate_ids: list[str]
    fixed_candidate_ids: list[str]
    local_cardinality: int
    rationale: list[str] = Field(default_factory=list)


class RunResult(StrictModel):
    run_id: str
    round_id: str
    status: RunStatus
    recommendations: list[CandidateBatch]
    verification: VerificationReport
    model_report: ModelFitReport
    predictions: list[ModelPrediction]
    solver_artifacts: list[SolverArtifact]
    warnings: list[str] = Field(default_factory=list)
    agent_events: list[dict[str, Any]] = Field(default_factory=list)
