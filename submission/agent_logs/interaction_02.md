# Agent/Skill 交互 02：任务校验与数据审计

- 日期：2026-07-28
- 输入任务：`batch_size=3`、`total_budget=5`、16 个候选、已有历史观测
- 调用链：`validate_design_spec → audit_dataset`
- 运行 ID：`demo-run-001/round_01`

## Agent 事件

```json
[
  {
    "tool_name": "validate_design_spec",
    "status": "success",
    "next_allowed_tools": ["audit_dataset"]
  },
  {
    "tool_name": "audit_dataset",
    "status": "started"
  },
  {
    "tool_name": "audit_dataset",
    "status": "success",
    "next_allowed_tools": ["fit_surrogate"]
  }
]
```

## 有效性

Agent 不允许跳过数据审计；审计成功后才放行代理模型拟合。输入数据的来源和合成数据边界见 `submission/docs/data_provenance.md`。
