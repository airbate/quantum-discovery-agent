# 结果分析与正确性说明

## 1. 运行环境

基础实验在 macOS 本地环境执行；单卡实验在竞赛 Docker 的 Biren106M（32,512 MiB）上执行，Driver/SUPA 1.11、Python 3.10.12、PyTorch 2.9.0、Qiskit 2.5.1、Aer 0.17.2。Qiskit Aer 在 CPU 上模拟线路，壁仞 GPU 通过 `torch_br` / SUPA 承担 QAOA 批量 QUBO 能量评分。

演示配置：16 个候选变量、批次大小 3、成本上限 5、QAOA `p=1`、128 shots、最多 8 次目标评估、无噪声模型。

## 2. 单样例演示

由 `scripts/run_demo.py --output artifacts/submission-demo.json` 生成：

| 项目 | 结果 |
| --- | --- |
| 状态 | `verified` |
| QAOA 后端 | `qiskit_aer+torch_supa`（壁仞集成运行） |
| QAOA 推荐 | `c08, c10, c13` |
| 选中数量 | 3 |
| 总成本 | 3.3（不超过 5） |
| 报告目标值 | 1.713725 |
| 独立重算值 | 1.713725 |
| 目标值绝对误差 | 0 |
| 硬约束 | 通过 |
| QAOA 线路宽度/深度 | 16 / 1 |
| shots / 目标评估次数 | 128 / 8 |
| 壁仞主 QAOA 求解耗时 | 约 1.389 秒 |
| 导出 artifact 数量 | 13 |

同一次运行还输出 3 个经典策略推荐，用于展示系统不是只给出单一黑盒答案。壁仞原始结果位于 `submission/results/biren_single_card/demo-result.json`，资源后端明确记录为 `qiskit_aer+torch_supa` 且 `fallback=false`。

<div style="break-before: page;"></div>

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

壁仞版本使用 `--qubo-device supa` 重跑 5 个种子，总墙钟时间为 25.19 秒；5/5 状态均为 `verified`，Warm Start 后端均为 `qiskit_aer+torch_supa`，最终目标值重算误差均为 0。

## 5. 失败案例也被保留

`penalty_qaoa` 在部分种子会产生不满足固定基数的样本；独立验证器将其标记为不可行（5 个种子中 2 个可行），不会静默转换成正式推荐。该对照用于证明约束验证是发布前的硬门槛。

<div style="break-before: page;"></div>

## 6. SUPA 正确性与性能

`run_supa_correctness.py` 对实际 demo QUBO 的 65,536 个 16 位输入做 CPU/SUPA 逐项对照，包含 16 个线性项和 112 个二次项：CPU 1.733 秒，SUPA 1.075 秒，加速约 1.612 倍；最大绝对误差为 `6.171e-5`，低于 FP32 对照阈值 `0.0001`。

GPU 分数用于期望值计算和加速评分，最终候选统一由 CPU 双精度重算与排序，因此集成 demo 的发布值误差仍为 0。所有运行均远低于单样例 10 分钟、完整评测 30 分钟建议上限。

## 7. 复现命令

```bash
python scripts/run_correctness.py
python scripts/run_demo.py --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json

# 壁仞竞赛容器
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
python3 scripts/run_supa_correctness.py --device supa
python3 scripts/run_demo.py --qubo-device supa --output artifacts/biren-demo.json
python3 scripts/run_benchmark.py --seeds 1,2,3,4,5 --qubo-device supa \
  --output artifacts/biren-benchmark.json
```
