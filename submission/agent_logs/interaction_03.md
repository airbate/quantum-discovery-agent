# Agent/Skill 交互 03：代理模型与 QUBO 编译

- 日期：2026-07-28
- 用户意图：在当前历史观测上估计候选产率和不确定性，并将多目标选择任务转换为量子优化问题。
- 调用链：`fit_surrogate → compile_qubo`
- 运行 ID：`demo-run-001/round_01`

## Agent 事件

```json
[
  {
    "tool_name": "fit_surrogate",
    "status": "success",
    "next_allowed_tools": ["compile_qubo"]
  },
  {
    "tool_name": "compile_qubo",
    "status": "success",
    "next_allowed_tools": ["solve_batch"]
  }
]
```

## 有效性

该步骤产生 `model_report.json`、`model_predictions.json`、`acquisition.json` 和 `qubo_problem.json`。QUBO 记录候选变量映射、固定基数、预算和二次多样性项，后续求解器不再直接读取自然语言。
