import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.models import QUBOProblem
from app.optimization.supa import SupaQUBOEvaluator


def make_problem() -> QUBOProblem:
    return QUBOProblem(
        problem_id="supa-test",
        variable_ids=["a", "b", "c"],
        linear={"a": 1.0, "b": -0.5, "c": 2.0},
        quadratic={"a|b": 0.25, "b|c": -1.5},
        constant=0.75,
        source_acquisition_id="fixture",
    )


def test_cpu_batch_evaluation_matches_worked_qubo_values():
    result = SupaQUBOEvaluator().evaluate(
        make_problem(),
        [[0, 0, 0], [1, 0, 1], [1, 1, 1]],
        device="cpu",
    )

    assert result.values == pytest.approx([0.75, 3.75, 2.0])
    assert result.backend == "python_cpu"
    assert result.fallback is False


def test_batch_evaluation_rejects_invalid_bitstrings():
    with pytest.raises(ValueError, match="binary and match"):
        SupaQUBOEvaluator().evaluate(make_problem(), [[1, 0]], device="cpu")


def test_auto_device_reports_cpu_fallback(monkeypatch):
    evaluator = SupaQUBOEvaluator()

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("no SUPA device")

    monkeypatch.setattr(evaluator, "_evaluate_supa", unavailable)
    result = evaluator.evaluate(make_problem(), [[1, 0, 1]], device="auto")

    assert result.backend == "python_cpu"
    assert result.fallback is True
    assert "no SUPA device" in result.warnings[0]


def test_correctness_cli_writes_submission_ready_report(tmp_path):
    output = tmp_path / "supa-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_supa_correctness.py",
            "--device",
            "cpu",
            "--batch-size",
            "16",
            "--output",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["correctness"]["max_abs_diff"] == pytest.approx(0.0)
    assert report["workload"]["bitstring_count"] == 16
    assert report["accelerator"]["backend"] == "python_cpu"
    assert report["accelerator"]["gpu_participated"] is False
    assert report["environment"]["requested_device"] == "cpu"
    assert report["correctness"]["lengths_match"] is True
    assert report["correctness"]["values_finite"] is True
    assert '"status": "passed"' in completed.stdout
