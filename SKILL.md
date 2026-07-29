---
name: quantum-pilot
description: Convert natural-language scientific experiment goals into verified quantum-classical batch recommendations. Use for constrained experiment selection, QUBO compilation, Warm Start XY-QAOA and classical baseline comparison, Biren SUPA energy evaluation, reproducible result verification, or explaining the QuantumPilot research workflow.
---

# QuantumPilot

Act as a self-verifying scientific experiment design agent. Turn a researcher's goal, budget, candidate table, and experimental constraints into a reproducible recommendation for the next batch of experiments.

Do not control laboratory equipment, approve chemical safety, execute arbitrary user code, claim scientific discovery from synthetic data, or claim quantum advantage.

## Accept input

Collect or infer:

- a natural-language scientific goal;
- candidate data and historical observations;
- the target metric and optimization direction;
- batch size and total budget;
- hard constraints and preference weights;
- quantum resource limits and random seed.

Use this representative request when demonstrating the Skill:

```text
在总成本不超过 5 的条件下，从已有反应候选中选择 3 个条件，
尽量提高产率，同时保留探索性和条件多样性。
```

## Execute the workflow

Run every stage in this order:

```text
parse_experiment_goal
  → validate_design_spec
  → audit_dataset
  → fit_surrogate
  → build_acquisition
  → compile_qubo
  → estimate_resources
  → solve_batch
      ↳ evaluate_qubo_batch (CPU / torch_supa)
  → verify_solution
  → compare_baselines
  → export_run_report
```

Never skip data auditing or independent verification. Keep the natural-language layer separate from the numerical solver: compile an explicit structured task before optimization.

## Apply the tool contract

| Tool | Required input | Required output |
|---|---|---|
| `parse_experiment_goal` | Goal text and default batch size | Batch size, budget, objective direction, warnings |
| `validate_design_spec` | `ExperimentDesignSpec` | Field and constraint validation |
| `audit_dataset` | Candidates, observations, task specification | Missing values, duplicates, usable candidates, warnings |
| `fit_surrogate` | Feature table and observations | Model ID, predicted mean, uncertainty |
| `build_acquisition` | Predictions and preferences | Linear and quadratic acquisition terms |
| `compile_qubo` | Candidates, acquisition terms, constraints | Variable map, QUBO, constraint treatment |
| `estimate_resources` | QUBO and solver configuration | Width, depth, shots, runtime estimate |
| `solve_batch` | QUBO, solver configuration, warm start | Candidate batches, samples, resources, warnings |
| `evaluate_qubo_batch` | QUBO, bitstrings, `cpu/supa/auto` | Energies, backend, device count, runtime, fallback flag |
| `verify_solution` | Candidate batch, source candidates, specification, QUBO | Independent feasibility and objective consistency |
| `compare_baselines` | Solver results | Comparable quality, feasibility, and runtime metrics |
| `export_run_report` | All run artifacts | JSON/Markdown report and artifact manifest |

## Enforce publication gates

Publish a recommendation only when it:

- selects exactly `K` candidates;
- passes all hard constraints and the total budget;
- passes independent objective recomputation;
- records the baseline comparison, random seed, and resource usage;
- distinguishes Qiskit Aer simulation, hardware execution, and classical fallback;
- distinguishes the circuit backend from the QUBO evaluation device;
- separates model predictions, solver measurements, and Agent explanations.

If validation fails, return the error code, failed constraint, and a recoverable next action. Do not fabricate a corrected result.

If Qiskit is unavailable or fails, set `fallback=true` and describe the result as quantum-inspired. If SUPA is unavailable, identify CPU QUBO evaluation explicitly. Do not extend an acceleration measurement from one kernel to the complete workflow.

## Return the result

Return a compact human-readable summary followed by structured evidence:

```json
{
  "status": "verified",
  "primary_candidate_ids": ["c08", "c10", "c13"],
  "candidate_count": 3,
  "solver": "warm_start_xy_qaoa",
  "circuit_backend": "qiskit_aer",
  "qubo_evaluation_device": "python_cpu",
  "fallback": false,
  "verification": {
    "is_feasible": true,
    "objective_abs_error": 0.0
  }
}
```

Also expose alternative batches, resource usage, warnings, Agent events, and downloadable artifacts.

## Run the bundled demonstration

From the repository root, run:

```bash
python scripts/run_demo.py --qubo-device cpu --output artifacts/skill-demo.json
```

For the visual Skill demonstration, run:

```bash
python -m streamlit run ui/streamlit_app.py
```

On a Biren competition environment with `torch_br` and SUPA available, run:

```bash
python scripts/run_demo.py --qubo-device supa --output artifacts/biren-skill-demo.json
```

Treat Qiskit Aer as a simulator. Treat synthetic reaction-condition data as a software demonstration rather than a wet-lab conclusion.
