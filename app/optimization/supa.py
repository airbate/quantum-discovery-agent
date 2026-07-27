from __future__ import annotations

import time
from typing import Literal

from app.domain.models import QUBOBatchEvaluation, QUBOProblem
from app.optimization.qubo import utility_for_bitstring


class SupaQUBOEvaluator:
    """Evaluate QUBO bitstrings on the CPU or a torch_br SUPA device."""

    def evaluate(
        self,
        problem: QUBOProblem,
        bitstrings: list[list[int]],
        device: Literal["auto", "cpu", "supa"] = "auto",
    ) -> QUBOBatchEvaluation:
        self._validate(bitstrings, len(problem.variable_ids))
        if device == "cpu":
            return self._evaluate_cpu(problem, bitstrings)
        try:
            return self._evaluate_supa(problem, bitstrings)
        except (ImportError, OSError, RuntimeError, AttributeError) as error:
            if device == "supa":
                raise RuntimeError(f"SUPA evaluation failed: {type(error).__name__}: {error}") from error
            result = self._evaluate_cpu(problem, bitstrings)
            result.fallback = True
            result.warnings.append(
                f"SUPA unavailable; used CPU: {type(error).__name__}: {error}"
            )
            return result

    @staticmethod
    def _validate(bitstrings: list[list[int]], width: int) -> None:
        if any(len(bits) != width or any(bit not in (0, 1) for bit in bits) for bits in bitstrings):
            raise ValueError("bitstrings must be binary and match QUBO variable count")

    @staticmethod
    def _evaluate_cpu(
        problem: QUBOProblem,
        bitstrings: list[list[int]],
    ) -> QUBOBatchEvaluation:
        started = time.perf_counter()
        values = [utility_for_bitstring(bits, problem) for bits in bitstrings]
        return QUBOBatchEvaluation(
            values=values,
            backend="python_cpu",
            wall_time_seconds=time.perf_counter() - started,
        )

    @staticmethod
    def _evaluate_supa(
        problem: QUBOProblem,
        bitstrings: list[list[int]],
    ) -> QUBOBatchEvaluation:
        import torch
        import torch_br  # noqa: F401  # registers torch.supa

        device_count = int(torch.supa.device_count())
        if device_count < 1:
            raise RuntimeError("torch_br reports no SUPA device")

        started = time.perf_counter()
        bits = (
            torch.tensor(bitstrings, dtype=torch.float32, device="supa")
            if bitstrings
            else torch.empty((0, len(problem.variable_ids)), dtype=torch.float32, device="supa")
        )
        linear = torch.tensor(
            [problem.linear.get(variable_id, 0.0) for variable_id in problem.variable_ids],
            dtype=torch.float32,
            device="supa",
        )
        values = bits.matmul(linear) + float(problem.constant)
        positions = {variable_id: index for index, variable_id in enumerate(problem.variable_ids)}
        for key, coefficient in problem.quadratic.items():
            left, right = key.split("|", 1)
            values = values + float(coefficient) * bits[:, positions[left]] * bits[:, positions[right]]
        torch.supa.synchronize()
        host_values = [float(value) for value in values.cpu().tolist()]
        return QUBOBatchEvaluation(
            values=host_values,
            backend="torch_supa",
            device_count=device_count,
            wall_time_seconds=time.perf_counter() - started,
        )
