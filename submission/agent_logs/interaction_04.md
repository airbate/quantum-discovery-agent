# Agent/Skill 交互 04：量子求解与基线比较

- 日期：2026-07-28
- 用户意图：运行可行 Warm Start XY-QAOA，并和经典方法比较。
- 调用：`solve_batch`
- 量子后端：`qiskit_aer`
- 配置：16 qubits、`p=1`、128 shots、8 次目标函数评估、`fallback=false`

## Agent 输出摘要

```json
{
  "solver_kind": "warm_start_xy_qaoa",
  "candidate_ids": ["c08", "c10", "c13"],
  "predicted_objective": 1.713724895276412,
  "backend": "qiskit_aer",
  "quantum_width": 16,
  "circuit_depth": 1,
  "shots": 128,
  "fallback": false
}
```

同一轮还运行 `enumeration`、`greedy`、`classical_bo`、`simulated_annealing` 和 `penalty_qaoa`，结果写入 `solver_results.json`。系统不会把 Qiskit Aer 模拟结果描述成量子硬件或量子优势。
