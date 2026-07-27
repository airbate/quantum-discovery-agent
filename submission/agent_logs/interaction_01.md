# Agent/Skill 交互 01：自然语言目标解析

- 日期：2026-07-28
- 角色：科研用户 → Q-Discovery Agent
- 用户输入：`在总成本不超过 5 的条件下，选择 3 个实验，尽量提高产率，同时兼顾探索性和多样性。`
- 调用：`parse_experiment_goal`

## Agent 输出

```json
{
  "batch_size": 3,
  "total_budget": 5.0,
  "objective_direction": "maximize",
  "objective_text": "在总成本不超过 5 的条件下，选择 3 个实验，尽量提高产率，同时兼顾探索性和多样性。",
  "warnings": []
}
```

## 有效性

解析结果被写入结构化任务规格，后续步骤使用同一批次大小、预算和目标方向。解析器只提取安全的数值字段，不执行自然语言中的代码。
