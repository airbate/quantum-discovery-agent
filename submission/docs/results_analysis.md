# 结果分析与正确性说明

## 1. 运行环境

本次可复现实验在 macOS 本地 Python 3.11 虚拟环境执行，安装项目的 `[dev,quantum]` 可选依赖；量子后端为 `qiskit_aer`，不是量子硬件。壁仞 GPU 尚未在本报告中实测，因此不能把本地 CPU/Aer 数字写成壁仞 GPU 性能。

演示配置：16 个候选变量、批次大小 3、成本上限 5、QAOA `p=1`、128 shots、最多 8 次目标评估、无噪声模型。

## 2. 单样例演示

由 `scripts/run_demo.py --output artifacts/submission-demo.json` 生成：

| 项目 | 结果 |
| --- | --- |
| 状态 | `verified` |
| QAOA 后端 | `qiskit_aer` |
| QAOA 推荐 | `c08, c10, c13` |
| 选中数量 | 3 |
| 总成本 | 3.3（不超过 5） |
| 报告目标值 | 1.713725 |
| 独立重算值 | 1.713725 |
| 目标值绝对误差 | 0 |
| 硬约束 | 通过 |
| QAOA 线路宽度/深度 | 16 / 1 |
| shots / 目标评估次数 | 128 / 8 |
| QAOA 求解耗时 | 约 0.378 秒 |
| 导出 artifact 数量 | 13 |

同一次运行还输出 3 个经典策略推荐，用于展示系统不是只给出单一黑盒答案。完整输入、QUBO、求解、验证和 Agent 事件位于 `artifacts/submission-demo.json` 及 `artifacts/demo-run-001/round_01/`。

## 3. 正确性验证

`scripts/run_correctness.py` 在 6 个候选中枚举固定选择 2 个的全部组合，共 15 个可行组合；每个组合均经过硬约束和目标值重算检查。随后执行完整服务链并断言：

- 状态为 `verified`；
- 推荐存在；
- 推荐批次可行；
- 目标值在独立重算后保持一致。

控制台结果：

```text
correctness passed: 15 feasible combinations; best=1.225782
```

## 4. 五种子稳定性评测

`scripts/run_benchmark.py --seeds 1,2,3,4,5` 的 5 个运行均通过验证，最终 QAOA 推荐的可行率为 100%。

| 求解器 | 目标值均值 | 目标值标准差 | 平均耗时（秒） | 可行率 |
| --- | ---: | ---: | ---: | ---: |
| enumeration | 1.989851 | 0.000000 | 0.00967 | 100% |
| greedy | 1.945732 | 0.000000 | 0.000078 | 100% |
| classical_bo | 1.945732 | 0.000000 | 0.000071 | 100% |
| simulated_annealing | 1.981027 | 0.017648 | 0.01356 | 100% |
| penalty_qaoa | 8.484807 | 5.635162 | 0.39300 | 40% |
| warm_start_xy_qaoa | 1.940606 | 0.068720 | 0.38813 | 100% |

在这个小规模合成实例上，精确枚举是上界参考，Warm Start XY-QAOA 的平均近似比为 0.9753，5 个种子的平均预测简单遗憾为 0.1305。该结果只说明当前实例和预算下的可复现行为，不证明量子优势。

## 5. 失败案例也被保留

`penalty_qaoa` 在部分种子会产生不满足固定基数的样本；独立验证器将其标记为不可行（5 个种子中 2 个可行），不会静默转换成正式推荐。该对照用于证明约束验证是发布前的硬门槛。

## 6. 性能边界

本次本地墙钟记录：演示脚本约 1.05 秒，多种子评测约 4.29 秒，均低于赛题建议的 10 分钟单样例和 30 分钟完整评测上限。机器、Python、Qiskit Aer 版本变化会影响具体数字；提交时应在目标壁仞 GPU 环境重新记录单卡日志。

## 7. 复现命令

```bash
python scripts/run_correctness.py
python scripts/run_demo.py --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json
```
