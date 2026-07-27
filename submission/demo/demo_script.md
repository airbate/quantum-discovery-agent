# 3 分钟演示脚本

## 0:00–0:20 问题

展示一张候选实验条件表，说明预算只能选择 3 个条件。强调目标不是让 Agent 直接替研究人员做化学判断，而是组织“数据—模型—量子优化—验证”的实验设计闭环。

## 0:20–0:45 自然语言输入

输入：

> 在总成本不超过 5 的条件下，选择 3 个实验，尽量提高产率，同时兼顾探索性和多样性。

展示解析出的 `batch_size=3`、`total_budget=5` 和 `maximize`。

## 0:45–1:20 Agent 调用链

依次展示：

```text
validate_design_spec
→ audit_dataset
→ fit_surrogate
→ compile_qubo
→ solve_batch
→ verify_solution
→ export_run_report
```

说明每一步的输入、输出和放行条件，打开 `submission/agent_logs/` 中的五段记录。

## 1:20–2:10 量子求解

展示 QUBO 变量数 16、QAOA 深度 1、128 shots 和 Qiskit Aer 后端。展示 Warm Start XY-QAOA 推荐 `c08,c10,c13`，并说明它同时输出经典基线，不把 Aer 模拟器说成量子硬件。

## 2:10–2:40 独立验证

展示：

- 恰好选择 3 个候选；
- 总成本 3.3，不超过 5；
- 目标值独立重算误差为 0；
- 状态为 `verified`；
- `fallback=false`。

打开 `artifacts/submission-demo.json` 或 `submission/results/verification_report.md`。

## 2:40–3:00 边界与复现

说明演示使用合成数据，只证明软件链路；正式研究需要替换为公开/授权数据，并在壁仞 GPU 环境重新记录单卡性能。最后运行：

```bash
python scripts/run_correctness.py
python scripts/run_demo.py --output artifacts/submission-demo.json
```
