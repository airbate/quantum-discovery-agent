from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.features import FeatureEncoder
from app.data.ingest import load_candidates_csv
from app.domain.models import ExperimentDesignSpec
from app.modeling.acquisition import build_acquisition
from app.modeling.surrogate import NearestEnsembleSurrogate
from app.optimization.qubo import compile_qubo
from app.optimization.supa import SupaQUBOEvaluator


def summarize_evaluation(result) -> dict:
    canonical = ",".join(f"{value:.12g}" for value in result.values).encode("utf-8")
    return {
        "backend": result.backend,
        "device_count": result.device_count,
        "wall_time_seconds": result.wall_time_seconds,
        "fallback": result.fallback,
        "warnings": result.warnings,
        "value_count": len(result.values),
        "value_min": min(result.values, default=None),
        "value_max": max(result.values, default=None),
        "value_samples": result.values[:8],
        "values_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def load_demo_problem(config_path: str, data_path: str):
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    spec = ExperimentDesignSpec.model_validate(payload)
    candidates, observations = load_candidates_csv(
        data_path,
        candidate_id_column=spec.candidate_source.candidate_id_column,
        target_column=spec.candidate_source.observed_target_column,
        feature_columns=spec.candidate_source.feature_columns,
    )
    history = observations[: max(2, len(observations) // 2)]
    table = FeatureEncoder(spec.candidate_source.feature_columns).fit(candidates).transform(candidates)
    model = NearestEnsembleSurrogate()
    model.fit(history, table)
    acquisition = build_acquisition(candidates, model.predict(table), spec.preferences)
    return compile_qubo(candidates, spec, acquisition)


def generate_bitstrings(width: int, count: int) -> list[list[int]]:
    maximum = 1 << width
    if count < 1 or count > maximum:
        raise ValueError(f"batch size must be between 1 and {maximum} for width {width}")
    return [[(value >> index) & 1 for index in range(width)] for value in range(count)]


def collect_environment(requested_device: str) -> dict:
    environment = {
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "requested_device": requested_device,
    }
    for distribution in ("qiskit", "qiskit-aer"):
        try:
            environment[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            environment[distribution] = None
    if requested_device in {"supa", "auto"}:
        try:
            import torch
            import torch_br

            environment.update(
                {
                    "torch": torch.__version__,
                    "torch_br": getattr(torch_br, "__file__", "installed"),
                    "supa_device_count": int(torch.supa.device_count()),
                }
            )
        except (ImportError, OSError, RuntimeError, AttributeError) as error:
            environment["supa_probe_error"] = f"{type(error).__name__}: {error}"
    return environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare CPU and Biren SUPA QUBO evaluation")
    parser.add_argument("--config", default="data/examples/demo_config.json")
    parser.add_argument("--data", default="data/examples/demo_candidates.csv")
    parser.add_argument("--device", choices=("cpu", "supa", "auto"), default="supa")
    parser.add_argument("--batch-size", type=int, default=65_536)
    parser.add_argument("--tolerance", type=float, default=1e-4)
    parser.add_argument("--output", default="artifacts/supa-correctness.json")
    args = parser.parse_args()

    problem = load_demo_problem(args.config, args.data)
    bitstrings = generate_bitstrings(len(problem.variable_ids), args.batch_size)
    evaluator = SupaQUBOEvaluator()
    cpu = evaluator.evaluate(problem, bitstrings, device="cpu")
    accelerated = evaluator.evaluate(problem, bitstrings, device=args.device)
    lengths_match = len(cpu.values) == len(accelerated.values) == len(bitstrings)
    values_finite = all(math.isfinite(value) for value in cpu.values + accelerated.values)
    max_abs_diff = (
        max(
            (abs(reference - observed) for reference, observed in zip(cpu.values, accelerated.values)),
            default=0.0,
        )
        if lengths_match and values_finite
        else None
    )
    passed = lengths_match and values_finite and max_abs_diff is not None and max_abs_diff <= args.tolerance
    speedup = (
        cpu.wall_time_seconds / accelerated.wall_time_seconds
        if accelerated.wall_time_seconds > 0
        else None
    )
    report = {
        "status": "passed" if passed else "failed",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": collect_environment(args.device),
        "workload": {
            "problem_id": problem.problem_id,
            "variable_count": len(problem.variable_ids),
            "linear_term_count": len(problem.linear),
            "quadratic_term_count": len(problem.quadratic),
            "bitstring_count": len(bitstrings),
        },
        "cpu": summarize_evaluation(cpu),
        "accelerator": {
            **summarize_evaluation(accelerated),
            "requested_device": args.device,
            "gpu_participated": accelerated.backend == "torch_supa",
        },
        "correctness": {
            "max_abs_diff": max_abs_diff,
            "tolerance": args.tolerance,
            "lengths_match": lengths_match,
            "values_finite": values_finite,
            "cpu_accelerator_match": passed,
        },
        "performance": {"cpu_to_accelerator_speedup": speedup},
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
