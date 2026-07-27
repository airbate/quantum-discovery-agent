from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass

from app.data.audit import audit_candidates
from app.data.features import FeatureEncoder
from app.domain.models import (
    Candidate,
    CandidateBatch,
    ExperimentDesignSpec,
    ModelFitReport,
    ModelPrediction,
    PreferenceWeights,
    RunResult,
    RunStatus,
    SolverArtifact,
    SolverConfig,
    SolverKind,
)
from app.modeling.acquisition import build_acquisition
from app.modeling.surrogate import NearestEnsembleSurrogate
from app.optimization.baselines import (
    ClassicalBatchBOSolver,
    EnumerationSolver,
    GreedySolver,
    SimulatedAnnealingSolver,
)
from app.optimization.neighborhoods import build_neighborhoods
from app.optimization.qaoa import QAOAAdapter
from app.optimization.qubo import compile_qubo, utility_for_bitstring
from app.optimization.warm_start import build_warm_start
from app.runtime.artifacts import ArtifactStore
from app.verification.feasibility import verify_bitstring
from app.verification.metrics import (
    baseline_result,
    batch_diversity,
    simple_regret,
    stability_summary,
)


@dataclass
class PipelineArtifacts:
    audit: dict
    feature_table: object
    model_report: ModelFitReport
    predictions: list[ModelPrediction]
    acquisition: dict
    problem: object
    warm_start: object


class ExperimentService:
    """Application service implementing one complete active-learning round."""

    def __init__(self, artifact_store=None):
        self.artifact_store = artifact_store or ArtifactStore("artifacts")

    def run_round(
        self,
        spec: ExperimentDesignSpec,
        candidates: list[Candidate],
        observations: list,
        round_id: str = "round_01",
        include_enumeration: bool = True,
    ) -> RunResult:
        audit = audit_candidates(candidates, observations, spec)
        available = [candidate for candidate in candidates if candidate.availability]
        encoder = FeatureEncoder(spec.candidate_source.feature_columns).fit(available)
        feature_table = encoder.transform(available)
        model = NearestEnsembleSurrogate()
        model_report = model.fit(observations, feature_table)
        predictions = model.predict(feature_table)
        acquisition = build_acquisition(
            available,
            predictions,
            spec.preferences,
            spec.objective.direction,
            feature_table.rows,
        )
        problem = compile_qubo(available, spec, acquisition)
        warm_start = build_warm_start(problem, available, spec, spec.solver.seed)

        classical_artifacts: list[SolverArtifact] = []
        combination_count = self._combination_count(len(available), spec.cardinality())
        if include_enumeration and combination_count <= 50_000:
            classical_artifacts.append(EnumerationSolver().solve(problem, available, spec, spec.solver.seed))
        classical_artifacts.append(GreedySolver().solve(problem, available, spec, spec.solver.seed))
        classical_artifacts.append(ClassicalBatchBOSolver().solve(problem, available, spec, spec.solver.seed))
        classical_artifacts.append(SimulatedAnnealingSolver().solve(problem, available, spec, spec.solver.seed))
        if len(available) <= spec.solver.max_quantum_width:
            penalty_config = spec.solver.model_copy(update={"kind": SolverKind.PENALTY_QAOA})
            classical_artifacts.append(QAOAAdapter(available, spec).solve(problem, penalty_config, None))

        qaoa_artifacts = self._solve_quantum(
            problem,
            available,
            spec,
            predictions,
            warm_start,
            feature_table.candidate_ids,
            feature_table.rows,
        )
        all_artifacts = classical_artifacts + qaoa_artifacts
        best_qaoa = max(qaoa_artifacts, key=lambda artifact: artifact.best_value)
        report = verify_bitstring(
            best_qaoa.best_bitstring,
            available,
            spec,
            problem,
            best_qaoa.best_value,
        )
        report.baseline_comparison = [baseline_result(artifact, available, spec) for artifact in all_artifacts]
        report.stability = stability_summary(qaoa_artifacts, available, spec)
        exact_values = [
            artifact.best_value
            for artifact in classical_artifacts
            if artifact.solver_kind == SolverKind.ENUMERATION
        ]
        report.metrics = {
            "batch_diversity": batch_diversity(best_qaoa.best_bitstring, available),
            "approximation_ratio": (
                best_qaoa.best_value / max(exact_values)
                if exact_values and max(exact_values) > 0
                else 0.0
            ),
            "feasible_rate": report.stability.feasible_rate,
            "predicted_simple_regret": simple_regret(
                [candidate.candidate_id for bit, candidate in zip(best_qaoa.best_bitstring, available) if bit],
                [(item.candidate_id, item.mean) for item in predictions],
            ),
        }
        pareto_artifacts = self._profile_artifacts(spec, available, predictions, feature_table.rows)
        recommendations = self._recommendations(
            spec,
            available,
            predictions,
            problem,
            best_qaoa,
            classical_artifacts,
            pareto_artifacts,
        )
        status = RunStatus.VERIFIED if report.status in {"passed", "warning"} else RunStatus.FAILED
        warnings = list(model_report.warnings) + list(best_qaoa.warnings) + list(best_qaoa.resource_usage.warnings)
        result = RunResult(
            run_id=spec.run_id,
            round_id=round_id,
            status=status,
            recommendations=recommendations,
            verification=report,
            model_report=model_report,
            predictions=predictions,
            solver_artifacts=all_artifacts,
            warnings=warnings,
        )
        self._persist_artifacts(
            spec,
            round_id,
            audit,
            feature_table,
            model_report,
            predictions,
            acquisition,
            problem,
            warm_start,
            result,
        )
        return result

    def _persist_artifacts(
        self,
        spec,
        round_id,
        audit,
        feature_table,
        model_report,
        predictions,
        acquisition,
        problem,
        warm_start,
        result,
    ) -> None:
        """Persist every stage as JSON so a report never depends on UI state."""
        artifacts = {
            "input_spec": spec.model_dump(mode="json"),
            "data_audit": audit,
            "feature_table": feature_table.model_dump(mode="json"),
            "model_report": model_report.model_dump(mode="json"),
            "model_predictions": [item.model_dump(mode="json") for item in predictions],
            "acquisition": acquisition,
            "qubo_problem": problem.model_dump(mode="json"),
            "warm_start": warm_start.model_dump(mode="json"),
            "solver_results": [item.model_dump(mode="json") for item in result.solver_artifacts],
            "recommendations": [item.model_dump(mode="json") for item in result.recommendations],
            "verification_report": result.verification.model_dump(mode="json"),
            "agent_events": result.agent_events,
        }
        artifact_ids = []
        for name, payload in artifacts.items():
            artifact_ids.append(self.artifact_store.write_json(spec.run_id, round_id, name, payload))
        config_hash = hashlib.sha256(
            json.dumps(spec.model_dump(mode="json"), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        manifest_id = self.artifact_store.write_json(
            spec.run_id,
            round_id,
            "manifest",
            {
                "run_id": spec.run_id,
                "round_id": round_id,
                "status": result.status.value,
                "dataset_id": spec.candidate_source.dataset_id,
                "config_hash": config_hash,
                "artifact_ids": artifact_ids,
                "dependency_versions": {
                    "python": "3.10+",
                    "qiskit": "optional",
                    "torch_br_supa": "optional_competition_backend",
                },
            },
        )
        result.verification.artifact_ids = artifact_ids + [manifest_id]

    def _solve_quantum(
        self,
        problem,
        candidates: list[Candidate],
        spec: ExperimentDesignSpec,
        predictions: list[ModelPrediction],
        warm_start,
        feature_ids: list[str],
        feature_rows: list[list[float]],
    ) -> list[SolverArtifact]:
        if len(candidates) <= spec.solver.max_quantum_width:
            adapter = QAOAAdapter(candidates, spec)
            return [adapter.solve(problem, spec.solver, warm_start)]
        neighborhoods = build_neighborhoods(
            candidates,
            predictions,
            warm_start,
            spec.solver.max_quantum_width,
            count=3,
        )
        prediction_by_id = {item.candidate_id: item for item in predictions}
        artifacts: list[SolverArtifact] = []
        for neighborhood in neighborhoods:
            local_candidates = [
                candidate for candidate in candidates if candidate.candidate_id in neighborhood.active_candidate_ids
            ]
            local_predictions = [prediction_by_id[item.candidate_id] for item in local_candidates]
            local_rows = [
                row for candidate_id, row in zip(feature_ids, feature_rows)
                if candidate_id in neighborhood.active_candidate_ids
            ]
            local_acquisition = build_acquisition(
                local_candidates,
                local_predictions,
                spec.preferences,
                spec.objective.direction,
                local_rows,
            )
            local_problem = compile_qubo(local_candidates, spec, local_acquisition)
            local_warm = build_warm_start(local_problem, local_candidates, spec, spec.solver.seed)
            local_spec = copy.deepcopy(spec)
            local_spec.solver = SolverConfig(**spec.solver.model_dump(exclude={"max_quantum_width"}), max_quantum_width=len(local_candidates))
            local_artifact = QAOAAdapter(local_candidates, local_spec).solve(local_problem, local_spec.solver, local_warm)
            global_bits = [
                int(candidate.candidate_id in {
                    local_candidates[index].candidate_id
                    for index, bit in enumerate(local_artifact.best_bitstring)
                    if bit
                })
                for candidate in candidates
            ]
            local_artifact.best_bitstring = global_bits
            local_artifact.best_value = utility_for_bitstring(global_bits, problem)
            local_artifact.samples = [
                {
                    **sample,
                    "bitstring": [
                        int(candidate.candidate_id in {
                            local_candidates[index]
                            .candidate_id
                            for index, bit in enumerate(sample.get("bitstring", []))
                            if bit
                        })
                        for candidate in candidates
                    ],
                }
                for sample in local_artifact.samples
            ]
            local_artifact.resource_usage.warnings.append(neighborhood.neighborhood_id)
            artifacts.append(local_artifact)
        return artifacts

    @staticmethod
    def _combination_count(n: int, k: int) -> int:
        if k < 0 or k > n:
            return 0
        result = 1
        for index in range(1, min(k, n - k) + 1):
            result = result * (n - index + 1) // index
        return result

    def _recommendations(
        self,
        spec: ExperimentDesignSpec,
        candidates: list[Candidate],
        predictions: list[ModelPrediction],
        problem,
        primary: SolverArtifact,
        baselines: list[SolverArtifact],
        alternatives: list[tuple[str, SolverArtifact]],
    ) -> list[CandidateBatch]:
        prediction_by_id = {item.candidate_id: item for item in predictions}
        batches: list[CandidateBatch] = []
        artifacts = [("primary", primary)] + alternatives + [
            (artifact.solver_kind.value, artifact) for artifact in baselines
        ]
        seen: set[tuple[str, ...]] = set()
        for index, (strategy, artifact) in enumerate(artifacts):
            selected = tuple(
                candidate.candidate_id
                for bit, candidate in zip(artifact.best_bitstring, candidates)
                if bit
            )
            if len(selected) != spec.cardinality() or selected in seen:
                continue
            seen.add(selected)
            chosen = [candidate for candidate in candidates if candidate.candidate_id in selected]
            mean = sum(prediction_by_id[item.candidate_id].mean for item in chosen) / len(chosen)
            uncertainty = sum(prediction_by_id[item.candidate_id].std for item in chosen) / len(chosen)
            batches.append(
                CandidateBatch(
                    batch_id=f"batch_{len(batches):02d}",
                    strategy=strategy,
                    candidate_ids=list(selected),
                    predicted_components={
                        "mean": mean,
                        "uncertainty": uncertainty,
                        "diversity": batch_diversity(artifact.best_bitstring, candidates),
                        "cost": sum(item.cost for item in chosen),
                        "risk": sum(item.risk for item in chosen),
                    },
                    predicted_objective=utility_for_bitstring(artifact.best_bitstring, problem),
                    solver_kind=artifact.solver_kind,
                    sample_probability=(
                        next(
                            (
                                sample.get("probability")
                                for sample in artifact.samples
                                if sample.get("bitstring") == artifact.best_bitstring
                            ),
                            None,
                        )
                    ),
                    resource_usage=artifact.resource_usage,
                )
            )
            if len(batches) >= 4:
                break
        return batches

    def _profile_artifacts(
        self,
        spec: ExperimentDesignSpec,
        candidates: list[Candidate],
        predictions: list[ModelPrediction],
        feature_rows: list[list[float]],
    ) -> list[tuple[str, SolverArtifact]]:
        profiles = [
            (
                "high_yield",
                PreferenceWeights(exploitation=0.75, exploration=0.05, diversity=0.1, cost=0.05, risk=0.05),
            ),
            (
                "high_information",
                PreferenceWeights(exploitation=0.15, exploration=0.45, diversity=0.3, cost=0.05, risk=0.05),
            ),
            (
                "low_cost_risk",
                PreferenceWeights(exploitation=0.3, exploration=0.1, diversity=0.15, cost=0.2, risk=0.25),
            ),
        ]
        artifacts: list[tuple[str, SolverArtifact]] = []
        for name, weights in profiles:
            acquisition = build_acquisition(
                candidates,
                predictions,
                weights,
                spec.objective.direction,
                feature_rows,
            )
            problem = compile_qubo(candidates, spec, acquisition)
            artifact = GreedySolver().solve(problem, candidates, spec, spec.solver.seed)
            artifacts.append((name, artifact))
        return artifacts
