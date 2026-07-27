from __future__ import annotations

import math
import random
import time

from app.domain.models import (
    Candidate,
    ExperimentDesignSpec,
    QUBOProblem,
    ResourceUsage,
    SolverArtifact,
    SolverConfig,
    SolverKind,
    WarmStartArtifact,
)
from app.optimization.constraints import is_feasible
from app.optimization.qubo import utility_for_bitstring
from app.optimization.supa import SupaQUBOEvaluator


class QAOAAdapter:
    """QAOA adapter with a real Qiskit path and a labeled deterministic fallback."""

    def __init__(self, candidates: list[Candidate], spec: ExperimentDesignSpec):
        self.candidates = candidates
        self.spec = spec
        self.qubo_evaluator = SupaQUBOEvaluator()

    def solve(
        self,
        problem: QUBOProblem,
        config: SolverConfig,
        warm_start: WarmStartArtifact | None = None,
    ) -> SolverArtifact:
        if len(problem.variable_ids) > config.max_quantum_width:
            raise ValueError(
                f"compiled problem has {len(problem.variable_ids)} variables, limit is {config.max_quantum_width}"
            )
        if config.backend in {"auto", "qiskit", "aer"}:
            try:
                return self._qiskit_solve(problem, config, warm_start)
            except ImportError:
                pass
            except (OSError, RuntimeError, ValueError) as error:
                # The result is still useful for an offline demo, but the warning
                # makes the degradation visible to the UI and report.
                fallback = self._fallback_solve(problem, config, warm_start)
                fallback.warnings.append(f"qiskit backend failed: {type(error).__name__}: {error}")
                fallback.resource_usage.warnings.append("used classical fallback after quantum backend failure")
                return fallback
        return self._fallback_solve(problem, config, warm_start)

    def _fallback_solve(
        self,
        problem: QUBOProblem,
        config: SolverConfig,
        warm_start: WarmStartArtifact | None,
    ) -> SolverArtifact:
        """Quantum-inspired feasible sampler used when optional Qiskit is absent."""
        started = time.perf_counter()
        rng = random.Random(config.seed)
        feasible = [bits for bits in self._feasible_bits()]
        if not feasible:
            raise ValueError("no feasible bitstring exists")
        scores = [utility_for_bitstring(bits, problem) for bits in feasible]
        temperature = max(0.05, 1.0 / max(1, config.p))
        weights = [math.exp((score - max(scores)) / temperature) for score in scores]
        total = sum(weights)
        samples: list[dict] = []
        for _ in range(config.shots):
            index = self._weighted_index(weights, total, rng)
            samples.append({"bitstring": feasible[index], "value": scores[index], "probability": weights[index] / total})
        best = max(samples, key=lambda item: item["value"])
        return SolverArtifact(
            solver_kind=(
                SolverKind.WARM_START_XY_QAOA
                if config.kind == SolverKind.WARM_START_XY_QAOA
                else SolverKind.PENALTY_QAOA
            ),
            samples=samples,
            best_bitstring=list(best["bitstring"]),
            best_value=float(best["value"]),
            resource_usage=ResourceUsage(
                backend="quantum_inspired_fallback",
                quantum_width=len(problem.variable_ids),
                circuit_depth=config.p,
                shots=config.shots,
                objective_calls=config.max_objective_calls,
                wall_time_seconds=time.perf_counter() - started,
                fallback=True,
                warnings=["Qiskit is not installed; this is not a hardware/simulator QAOA result"],
            ),
            warnings=["install q-discovery-agent[quantum] to enable the Qiskit backend"],
        )

    def _weighted_index(self, weights: list[float], total: float, rng: random.Random) -> int:
        target = rng.random() * total
        running = 0.0
        for index, weight in enumerate(weights):
            running += weight
            if running >= target:
                return index
        return len(weights) - 1

    def _feasible_bits(self):
        from app.optimization.qubo import feasible_bitstrings

        return feasible_bitstrings(self.candidates, self.spec)

    def _qiskit_solve(
        self,
        problem: QUBOProblem,
        config: SolverConfig,
        warm_start: WarmStartArtifact | None,
    ) -> SolverArtifact:
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        started = time.perf_counter()
        width = len(problem.variable_ids)
        noise_model = None
        if config.noise_model == "depolarizing":
            from qiskit_aer.noise import NoiseModel, depolarizing_error

            noise_model = NoiseModel()
            noise_model.add_all_qubit_quantum_error(depolarizing_error(0.01, 1), ["rx", "rz", "h"])
            noise_model.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["rxx", "ryy", "rzz"])
        backend = AerSimulator(noise_model=noise_model)
        phase_problem = self._penalty_problem(problem) if config.kind == SolverKind.PENALTY_QAOA else problem
        angles = self._angle_candidates(config)
        search_shots = max(32, min(config.shots, 128))
        best_angles = angles[0]
        best_expectation = float("-inf")
        objective_calls = 0
        qubo_backends: set[str] = set()
        evaluation_warnings: list[str] = []
        qubo_fallback_used = False
        for angle_index, (gammas, betas) in enumerate(angles[: config.max_objective_calls]):
            counts = self._run_circuit(
                phase_problem,
                config,
                warm_start,
                gammas,
                betas,
                backend,
                shots=search_shots,
                seed=config.seed + angle_index,
                transpile=transpile,
            )
            objective_calls += 1
            expectation, evaluation = self._expected_value(
                counts,
                problem if config.kind != SolverKind.PENALTY_QAOA else phase_problem,
                search_shots,
                only_feasible=config.kind != SolverKind.PENALTY_QAOA,
                device=config.qubo_evaluation_device,
            )
            qubo_backends.add(evaluation.backend)
            evaluation_warnings.extend(evaluation.warnings)
            qubo_fallback_used = qubo_fallback_used or evaluation.fallback
            if expectation > best_expectation:
                best_expectation = expectation
                best_angles = (gammas, betas)
        counts = self._run_circuit(
            phase_problem,
            config,
            warm_start,
            best_angles[0],
            best_angles[1],
            backend,
            shots=config.shots,
            seed=config.seed + objective_calls + 1,
            transpile=transpile,
        )
        raw_samples: list[tuple[list[int], int, bool]] = []
        for raw_bits, count in counts.items():
            bits = [int(bit) for bit in raw_bits[::-1]]
            feasible = is_feasible(bits, self.candidates, self.spec)[0]
            if feasible:
                raw_samples.append((bits, count, True))
        if not raw_samples and config.kind == SolverKind.PENALTY_QAOA:
            # A penalty baseline may legitimately return no feasible sample;
            # keep the best raw sample so the verifier can report that failure
            # instead of silently converting it into a different algorithm.
            for raw_bits, count in counts.items():
                bits = [int(bit) for bit in raw_bits[::-1]]
                raw_samples.append((bits, count, is_feasible(bits, self.candidates, self.spec)[0]))
        if not raw_samples:
            raise ValueError("Qiskit returned no feasible samples")
        final_evaluation = self.qubo_evaluator.evaluate(
            problem,
            [bits for bits, _, _ in raw_samples],
            device=config.qubo_evaluation_device,
        )
        qubo_backends.add(final_evaluation.backend)
        evaluation_warnings.extend(final_evaluation.warnings)
        qubo_fallback_used = qubo_fallback_used or final_evaluation.fallback
        samples: list[dict] = []
        for (bits, count, feasible), value in zip(raw_samples, final_evaluation.values):
            canonical_value = utility_for_bitstring(bits, problem)
            sample = {
                "bitstring": bits,
                "value": canonical_value,
                "accelerated_value": value,
                "count": count,
                "probability": count / config.shots,
            }
            if config.kind == SolverKind.PENALTY_QAOA:
                sample["feasible"] = feasible
            samples.append(sample)
        best = max(samples, key=lambda item: item["value"])
        canonical_best_value = float(best["value"])
        scoring_backend = "+".join(sorted(qubo_backends))
        return SolverArtifact(
            solver_kind=config.kind,
            samples=samples,
            best_bitstring=list(best["bitstring"]),
            best_value=canonical_best_value,
            resource_usage=ResourceUsage(
                backend=f"qiskit_aer+{scoring_backend}",
                quantum_width=width,
                circuit_depth=config.p,
                shots=config.shots,
                objective_calls=objective_calls,
                wall_time_seconds=time.perf_counter() - started,
                fallback=qubo_fallback_used,
                warnings=list(dict.fromkeys(evaluation_warnings)),
            ),
            warnings=list(dict.fromkeys(evaluation_warnings)),
        )

    def _angle_candidates(self, config: SolverConfig) -> list[tuple[list[float], list[float]]]:
        rng = random.Random(config.seed)
        base_gamma = [math.pi / (4.0 * (layer + 1)) for layer in range(config.p)]
        base_beta = [math.pi / (4.0 * (layer + 1)) for layer in range(config.p)]
        candidates = [(base_gamma, base_beta)]
        for index in range(max(0, config.max_objective_calls - 1)):
            if config.angle_optimizer == "grid":
                scale = 0.5 + (index % 4) / 3.0
                gammas = [value * scale for value in base_gamma]
                betas = [value * (1.5 - 0.2 * (index % 4)) for value in base_beta]
            elif config.angle_optimizer == "random":
                gammas = [rng.uniform(-math.pi, math.pi) for _ in range(config.p)]
                betas = [rng.uniform(0.0, math.pi / 2.0) for _ in range(config.p)]
            else:
                # Budgeted Bayesian-style search: deterministic warm-start plus
                # shrinking RBF-like perturbations around it. The measured
                # expectation is still the source of truth for each proposal.
                scale = 0.35 / math.sqrt(index + 1)
                gammas = [value + rng.gauss(0.0, scale) for value in base_gamma]
                betas = [value + rng.gauss(0.0, scale) for value in base_beta]
            candidates.append((gammas, betas))
        return candidates

    def _run_circuit(
        self,
        problem,
        config,
        warm_start,
        gammas,
        betas,
        backend,
        shots,
        seed,
        transpile,
    ):
        from qiskit import QuantumCircuit

        width = len(problem.variable_ids)
        circuit = QuantumCircuit(width, width)
        if config.kind == SolverKind.PENALTY_QAOA:
            for index in range(width):
                circuit.h(index)
        else:
            initial = warm_start.bitstring if warm_start and len(warm_start.bitstring) == width else None
            for index in range(width):
                if initial and initial[index]:
                    circuit.x(index)
        for layer in range(config.p):
            beta, gamma = betas[layer], gammas[layer]
            if config.kind == SolverKind.PENALTY_QAOA:
                for index in range(width):
                    circuit.rx(2 * beta, index)
            else:
                for index in range(width - 1):
                    circuit.rxx(2 * beta, index, index + 1)
                    circuit.ryy(2 * beta, index, index + 1)
            for index, variable in enumerate(problem.variable_ids):
                coefficient = problem.linear.get(variable, 0.0)
                if coefficient:
                    circuit.rz(2 * gamma * coefficient, index)
            for key, coefficient in problem.quadratic.items():
                left, right = key.split("|", 1)
                left_index = problem.variable_ids.index(left)
                right_index = problem.variable_ids.index(right)
                circuit.rzz(2 * gamma * coefficient, left_index, right_index)
        circuit.measure(range(width), range(width))
        compiled = transpile(circuit, backend, seed_transpiler=seed)
        return backend.run(compiled, shots=shots, seed_simulator=seed).result().get_counts()

    def _expected_value(self, counts, problem, shots, only_feasible=True, device="cpu"):
        bitstrings: list[list[int]] = []
        weights: list[int] = []
        for raw_bits, count in counts.items():
            bits = [int(bit) for bit in raw_bits[::-1]]
            if not only_feasible or is_feasible(bits, self.candidates, self.spec)[0]:
                bitstrings.append(bits)
                weights.append(count)
        evaluation = self.qubo_evaluator.evaluate(problem, bitstrings, device=device)
        total = sum(count * value for count, value in zip(weights, evaluation.values))
        return total / max(1, shots), evaluation

    @staticmethod
    def _penalty_problem(problem: QUBOProblem) -> QUBOProblem:
        """Build the phase objective used by the standard X-Mixer baseline."""
        cardinality = int(problem.metadata.get("cardinality", 0))
        scale = max([abs(value) for value in problem.linear.values()] + [0.0])
        scale = max(scale, max([abs(value) for value in problem.quadratic.values()] + [0.0]), 1.0)
        penalty = scale * (len(problem.variable_ids) + 1)
        linear = dict(problem.linear)
        quadratic = dict(problem.quadratic)
        for variable in problem.variable_ids:
            linear[variable] = linear.get(variable, 0.0) - penalty * (1.0 - 2.0 * cardinality)
        for left_index, left in enumerate(problem.variable_ids):
            for right in problem.variable_ids[left_index + 1 :]:
                key = f"{left}|{right}"
                quadratic[key] = quadratic.get(key, 0.0) - 2.0 * penalty
        return problem.model_copy(update={"linear": linear, "quadratic": quadratic})
