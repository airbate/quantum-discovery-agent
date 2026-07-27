# 正确性验证报告

## 验证入口

```bash
python scripts/run_correctness.py
```

## 验证内容

1. 构造 6 个候选和 2 个历史观测；
2. 固定批次大小为 2、预算为 2；
3. 枚举全部 `C(6,2)=15` 个组合；
4. 对每个组合执行固定基数、预算、可用性和目标函数重算；
5. 运行完整 `ExperimentService`，确认状态为 `verified`，并检查最终推荐可行。

## 结果

```text
correctness passed: 15 feasible combinations; best=1.225782
```

演示运行的独立验证字段：

```json
{
  "status": "passed",
  "is_feasible": true,
  "objective_reported": 1.713724895276412,
  "objective_recomputed": 1.713724895276412,
  "objective_abs_error": 0.0,
  "hard_constraints": "passed"
}
```

验证器位于 `app/verification/feasibility.py`。任何不可行比特串或目标值不一致的结果都会被拒绝发布；错误不会被包装成成功推荐。

## 壁仞 SUPA 对照

```bash
python3 scripts/run_supa_correctness.py --device supa
```

对 demo QUBO 的 65,536 个比特串逐项比较 CPU 双精度参考值与 SUPA FP32 输出，最大绝对误差为 `6.171035430924121e-05`，低于 `1e-4` 阈值。集成 Agent demo 使用 SUPA 结果进行期望值计算和加速评分，再对最终样本执行 CPU 双精度重算与排序；最终验证状态为 `passed`，发布目标值误差为 `0.0`。
